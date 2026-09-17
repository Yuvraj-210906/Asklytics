import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import io
from file_parsers import parse_structured_file, parse_unstructured_file
from core_agent import SelfHealingAnalystEngine

app = FastAPI()

# Enable cross-origin communication so your HTML file can talk to the Python backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = SelfHealingAnalystEngine()

@app.post("/api/analyze")
async def analyze_data(
    files: list[UploadFile] = File(...),
    query: str = Form(...)
):
    try:
        context_parts = []
        execution_scope = {"pd": pd}
        has_tabular = False
        import plotly.express as px
        
        for idx, file in enumerate(files[:3]):
            file_bytes = await file.read()
            file_name = file.filename
            is_tabular = file_name.endswith(('.csv', '.xlsx'))
            
            if is_tabular:
                has_tabular = True
                if file_name.endswith('.csv'):
                    df = pd.read_csv(io.BytesIO(file_bytes))
                else:
                    df = pd.read_excel(io.BytesIO(file_bytes))
                
                df = df.dropna(how='all').loc[:, ~df.columns.str.contains('^Unnamed', case=False, na=False)]
                df.columns = df.columns.str.strip()
                
                df_var_name = f"df{idx+1}" if len(files) > 1 else "df"
                execution_scope[df_var_name] = df
                
                context_parts.append(
                    f"File {idx+1} ({file_name}) loaded as DataFrame '{df_var_name}'. "
                    f"Columns: {list(df.columns)}. "
                    f"Sample:\n{df.head(3).to_string()}\n"
                )
            else:
                from pypdf import PdfReader
                text_content = ""
                if file_name.endswith('.pdf'):
                    pdf_reader = PdfReader(io.BytesIO(file_bytes))
                    for page in pdf_reader.pages:
                        text_content += (page.extract_text() or "") + "\n"
                text_var_name = f"text{idx+1}" if len(files) > 1 else "text_content"
                execution_scope[text_var_name] = text_content
                context_parts.append(
                    f"File {idx+1} ({file_name}) loaded as string '{text_var_name}'. "
                    f"Content snippet:\n{text_content[:2000]}\n"
                )

        if has_tabular:
            execution_scope["px"] = px

        context = (
            "The user uploaded the following files:\n" + "\n".join(context_parts) + "\n"
            f"User Intent: {query}.\n"
            f"Write valid executable Python code processing the provided DataFrames/strings. "
            f"Assign descriptive string summaries to 'text_insight'. "
            f"If a chart is requested, assign a Plotly Express object figure to 'fig'. IMPORTANT: Before plotting, drop NaN/missing values for the plotted columns to prevent empty charts! "
            f"Also, assign a list of exactly 3 highly relevant follow-up analytical questions to a variable named 'suggested_queries'. These should be strings that guide the user to dig deeper based on the insight you just found."
        )

        generated_script = engine.generate_analysis_code(prompt_context=context)
        local_vars = engine.execute_safely(code_str=generated_script, global_vars=execution_scope)
        
        fig = local_vars.get('fig')
        analytical_text = local_vars.get('text_insight', "Data processing operation concluded successfully.")
        suggestions = local_vars.get('suggested_queries', [])
        
        chart_json = None
        if fig:
            import json
            from plotly.utils import PlotlyJSONEncoder
            chart_json = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

        return JSONResponse({
            "status": "success",
            "insight": analytical_text,
            "chart_data": chart_json,
            "suggestions": suggestions
        })

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/quick_insight")
async def quick_insight(files: list[UploadFile] = File(...)):
    try:
        context_parts = []
        execution_scope = {"pd": pd}
        file_names = []
        for idx, file in enumerate(files[:3]):
            file_bytes = await file.read()
            file_name = file.filename
            file_names.append(file_name)
            
            if file_name.endswith(('.csv', '.xlsx')):
                if file_name.endswith('.csv'):
                    df = pd.read_csv(io.BytesIO(file_bytes))
                else:
                    df = pd.read_excel(io.BytesIO(file_bytes))
                df_var_name = f"df{idx+1}" if len(files) > 1 else "df"
                execution_scope[df_var_name] = df
                context_parts.append(f"File '{file_name}' ({df_var_name}): shape {df.shape}, columns {list(df.columns)}")
            else:
                text_var_name = f"text{idx+1}" if len(files) > 1 else "text_content"
                context_parts.append(f"Document '{file_name}' loaded as '{text_var_name}'.")

        context = "Files uploaded:\n" + "\n".join(context_parts) + "\nGive ONE short, punchy sentence highlighting the overall data readiness or a key combined metric."
            
        prompt = (
            f"Context: {context}\n"
            "Write Python code that assigns exactly one string sentence to the variable 'text_insight'.\n"
            "Also, assign a list of exactly 4 short strings to the variable 'suggested_queries'. These must be highly specific, analytical questions the user could ask based on the context. If tabular, use actual column names from the context.\n"
        )
        
        generated_script = engine.generate_analysis_code(prompt_context=prompt)
        local_vars = engine.execute_safely(code_str=generated_script, global_vars=execution_scope)
        insight = local_vars.get('text_insight', f"Data loaded successfully from {', '.join(file_names)}.")
        suggestions = local_vars.get('suggested_queries', ["Summarize key trends", "Identify top outliers", "Show basic distributions", "Compute correlation matrix"])
        
        return JSONResponse({
            "status": "success", 
            "insight": insight,
            "suggestions": suggestions
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/dashboard")
async def generate_dashboard(files: list[UploadFile] = File(...)):
    try:
        file = files[0]
        file_bytes = await file.read()
        file_name = file.filename
        if not file_name.endswith(('.csv', '.xlsx')):
            return JSONResponse({"status": "error", "message": "Dashboards currently only support Tabular datasets."})
            
        if file_name.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))
            
        df = df.dropna(how='all').loc[:, ~df.columns.str.contains('^Unnamed', case=False, na=False)]
        df.columns = df.columns.str.strip()
        
        context = (
            f"Generate a comprehensive dashboard from this dataset. Columns: {list(df.columns)}.\n"
            f"Data sample:\n{df.head(3).to_string()}\n\n"
            "REQUIREMENTS:\n"
            "1. Write Python code to analyze the dataframe `df`.\n"
            "2. Assign a dictionary to `dashboard_data` with these EXACT keys:\n"
            "   - 'anomalies' (list of strings, 2 items max)\n"
            "   - 'trends' (list of strings, 2 items max)\n"
            "   - 'summary' (string paragraph managerial overview)\n"
            "   - 'chart1_title' (string describing fig1)\n"
            "   - 'chart2_title' (string describing fig2)\n"
            "   - 'dataset_description' (string 1-2 sentence description of the dataset and its apparent quality/status)\n"
            "3. You MUST generate exactly TWO Plotly express figures and assign them to the variables `fig1` and `fig2`. It is completely unacceptable to skip one. IMPORTANT: Choose the most impactful and appropriate chart types based on the data types (e.g., px.line for time series, px.scatter for correlation, px.bar for categories). Drop NaN/missing values before plotting to prevent empty charts.\n"
        )
        
        import plotly.express as px
        execution_scope = {"df": df, "px": px, "pd": pd}
        generated_script = engine.generate_analysis_code(prompt_context=context)
        local_vars = engine.execute_safely(code_str=generated_script, global_vars=execution_scope)
        
        dash_data = local_vars.get('dashboard_data', {})
        fig1 = local_vars.get('fig1')
        fig2 = local_vars.get('fig2')
        
        import json
        from plotly.utils import PlotlyJSONEncoder
        
        chart1_json = json.loads(json.dumps(fig1, cls=PlotlyJSONEncoder)) if fig1 else None
        chart2_json = json.loads(json.dumps(fig2, cls=PlotlyJSONEncoder)) if fig2 else None

        return JSONResponse({
            "status": "success",
            "anomalies": dash_data.get('anomalies', []),
            "trends": dash_data.get('trends', []),
            "summary": dash_data.get('summary', "Summary not available."),
            "chart1_title": dash_data.get('chart1_title', "Primary Visualization"),
            "chart2_title": dash_data.get('chart2_title', "Secondary Visualization"),
            "dataset_description": dash_data.get('dataset_description', "Tabular dataset analysis."),
            "chart1": chart1_json,
            "chart2": chart2_json
        })

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/dashboard_add")
async def add_dashboard_insight(
    files: list[UploadFile] = File(...),
    query: str = Form(...)
):
    try:
        file = files[0]
        file_bytes = await file.read()
        file_name = file.filename
        
        if not file_name.endswith(('.csv', '.xlsx')):
            return JSONResponse({"status": "error", "message": "Dashboards currently only support Tabular datasets."})
            
        if file_name.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))
            
        df = df.dropna(how='all').loc[:, ~df.columns.str.contains('^Unnamed', case=False, na=False)]
        df.columns = df.columns.str.strip()
        
        context = (
            f"The user wants to add a new insight to their dashboard. Columns: {list(df.columns)}.\n"
            f"Data sample:\n{df.head(3).to_string()}\n\n"
            f"User Request: {query}\n\n"
            "REQUIREMENTS:\n"
            "1. Write Python code to analyze `df`.\n"
            "2. If the user asks for a chart/plot/visualization, generate a Plotly Express figure and assign it to `fig`.\n"
            "3. If the user asks for a text summary, metric, or calculation, assign a string to `text_insight`.\n"
            "4. Only assign ONE of them (`fig` OR `text_insight`), based on the best way to answer the query.\n"
        )
        
        import plotly.express as px
        execution_scope = {"df": df, "px": px, "pd": pd}
        generated_script = engine.generate_analysis_code(prompt_context=context)
        local_vars = engine.execute_safely(code_str=generated_script, global_vars=execution_scope)
        
        fig = local_vars.get('fig')
        text_insight = local_vars.get('text_insight')
        
        if fig:
            import json
            from plotly.utils import PlotlyJSONEncoder
            chart_json = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
            return JSONResponse({"status": "success", "type": "chart", "content": chart_json})
        elif text_insight:
            return JSONResponse({"status": "success", "type": "text", "content": text_insight})
        else:
            return JSONResponse({"status": "error", "message": "Failed to generate a valid chart or text insight."})
            
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/dataset")
async def get_dataset(files: list[UploadFile] = File(...)):
    try:
        file = files[0]
        file_bytes = await file.read()
        file_name = file.filename
        
        if not file_name.endswith(('.csv', '.xlsx')):
            return JSONResponse({"status": "error", "message": "Dataset view only supports Tabular formats (.csv, .xlsx)."})
            
        if file_name.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))
            
        df = df.dropna(how='all').loc[:, ~df.columns.str.contains('^Unnamed', case=False, na=False)]
        df.columns = df.columns.str.strip()
        
        # Return all rows as requested
        df_head = df.fillna("")
        
        return JSONResponse({
            "status": "success",
            "columns": list(df_head.columns),
            "rows": df_head.to_dict(orient="records"),
            "total_rows": len(df)
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)