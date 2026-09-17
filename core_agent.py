import os
import pandas as pd
from google import genai

# To run this app, set your Gemini API key in your environment, or uncomment and paste it below:
# os.environ["GEMINI_API_KEY"] = "PASTE_YOUR_GEMINI_API_KEY_HERE"

class SelfHealingAnalystEngine:
    def __init__(self):
        # Initialize the Google GenAI client
        self.client = genai.Client()
        self.model_name = "gemini-2.5-flash"

    def generate_analysis_code(self, prompt_context: str, error_message: str = None) -> str:
        """Asks Gemini to write clean analytical code based on available variables."""
        system_instruction = (
            "You are an elite Data Scientist and expert Python developer. Your job is to output ONLY executable Python code.\n"
            "Do NOT wrap code blocks inside markdown text notation like ```python. Return ONLY raw code lines.\n\n"
            "STRICT ARCHITECTURAL EXECUTION RULES:\n"
            "1. You must save your verbal response/insight in a string variable named 'text_insight'.\n"
            "2. If the user query implies an observation, trend, distribution, comparison or explicitly asks for a chart, "
            "you MUST build a Plotly Express chart asset assigned to a variable named 'fig'.\n"
            "3. Example template format:\n"
            "   text_insight = 'The leading categories are...'\n"
            "   fig = px.bar(df, x='AnyColumnFound', y='AnyNumericColumn')"
        )
        
        user_prompt = f"Dataset Environment Blueprint:\n{prompt_context}\n\n"
        if error_message:
            user_prompt += f"⚠️ RUNTIME WARNING: CRITICAL PREVIOUS SCRIPT ATTEMPT FAILED WITH ERROR:\n{error_message}\nRewrite the syntax code to fix this exception safely.\n"
        
        user_prompt += "Generate pristine Python analysis code lines execution block:"
        
        # Call the Google Gemini API safely
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1
            )
        )
        
        return response.text.replace("```python", "").replace("```", "").strip()

    def execute_safely(self, code_str: str, global_vars: dict, max_retries=3):
        """Monitors and catches runtime errors during evaluation loops to achieve self-healing targets."""
        for attempt in range(max_retries):
            try:
                local_scope_vars = {}
                exec(code_str, global_vars, local_scope_vars)
                return local_scope_vars
            except Exception as runtime_error:
                error_log_trace = f"{type(runtime_error).__name__}: {str(runtime_error)}"
                if attempt == max_retries - 1:
                    raise Exception(f"Self-Correction processing threshold limits breached: {error_log_trace}")
                
                # Regenerate script with explicit error traceback context
                code_str = self.generate_analysis_code(prompt_context=code_str, error_message=error_log_trace)