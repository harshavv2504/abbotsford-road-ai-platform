from typing import List, Dict, Optional
import json
from openai import AsyncOpenAI
from app.config.llm_config import llm_config
from app.utils.logger import logger
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from datetime import datetime


load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "conversation_db")

class LLMService:
    """OpenAI API service"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI async client"""
        api_key = llm_config.get_api_key()
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
            logger.info("✅ OpenAI async client initialized")
        else:
            logger.warning("⚠️  OpenAI API key not found")
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 150,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Dict] = None
    ) -> Dict:
        """
        Generate response from OpenAI
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_instruction: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Optional list of function definitions for function calling
        
        Returns:
            Dict with response text and optional function_call info
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized. Check API key.")
        
        # Add system message if provided
        if system_instruction:
            messages = [{"role": "system", "content": system_instruction}] + messages
        
        # Build API call parameters
        api_params = {
            "model": llm_config.OPENAI_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add tools if provided
        if tools:
            api_params["tools"] = tools
            # Add tool_choice if provided
            if tool_choice:
                api_params["tool_choice"] = tool_choice

        # Make the API call
        response = await self.client.chat.completions.create(**api_params)
        
        message = response.choices[0].message
        
        # Print for debugging
        # print("Payload:")
        # print(json.dumps(api_params, indent=2))
        # print("\nResponse:")
        # print(response)

        # Log to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[MONGODB_DB_NAME]

        api_key = llm_config.get_api_key()

        # Extract API key (last 4 characters only for security)
        api_key_masked = f"...{api_key[-4:]}" if api_key else "unknown"
        
        # Prepare tool_calls data
        tool_calls_data = None
        if message.tool_calls:
            tool_calls_data = [{
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            } for tc in message.tool_calls]
        
        # Prepare log document
        log_document = {
            "timestamp": datetime.utcnow(),
            "api_key": api_key_masked,
            "api_params": api_params,
            "payload": {
                "model": api_params["model"],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "message_count": len(messages)
            },
            "response_msg": message.content,
            "usage_tokens": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "prompt_tokens_details": {
                    "cached_tokens": response.usage.prompt_tokens_details.cached_tokens if hasattr(response.usage, 'prompt_tokens_details') else 0
                },
                "completion_tokens_details": {
                    "reasoning_tokens": response.usage.completion_tokens_details.reasoning_tokens if hasattr(response.usage.completion_tokens_details, 'reasoning_tokens') else 0
                } if hasattr(response.usage, 'completion_tokens_details') else {}
            },
            "model": response.model,
            "tool_calls": tool_calls_data,
            "finish_reason": response.choices[0].finish_reason,
            "response_id": response.id
        }
        
        result = await db.api_logger.insert_one(log_document)
        
        # Close MongoDB connection
        client.close()
        
        # Check if there's a function call
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            return {
                "type": "function_call",
                "function_name": tool_call.function.name,
                "function_args": tool_call.function.arguments,
                "tool_call_id": tool_call.id,
                "content": message.content,
                "assistant_message": {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }]
                }
            }
        
        # Regular text response
        return {
            "type": "text",
            "content": message.content
        }
    
    async def generate_response_with_function_result(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        function_name: str = None,
        function_result: Dict = None,
        tool_call_id: str = None,
        function_args: str = None,
        temperature: float = 0.7,
        max_tokens: int = 150
    ) -> Dict:
        """
        Generate response after function execution by sending result back to LLM
        
        Args:
            messages: Original conversation messages
            system_instruction: System prompt
            function_name: Name of the function that was called
            function_result: Result from the function execution
            tool_call_id: ID of the tool call
            function_args: Original function arguments (JSON string)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Dict with final response text
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized. Check API key.")
        
        # Add system message if provided
        if system_instruction:
            messages = [{"role": "system", "content": system_instruction}] + messages
        
        # Add the assistant's message with tool_calls (required by OpenAI)
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": tool_call_id,
                "type": "function",
                "function": {
                    "name": function_name,
                    "arguments": function_args
                }
            }]
        })
        
        # Add the function result as a tool message
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": function_name,
            "content": json.dumps(function_result)
        })
        
        # Build API call parameters
        api_params = {
            "model": llm_config.OPENAI_MODEL,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens is not None:
            api_params["max_tokens"] = max_tokens
        
        response = self.client.chat.completions.create(**api_params)
        
        message = response.choices[0].message
        
        # Return the final response
        return {
            "type": "text",
            "content": message.content
        }


# Singleton instance
llm_service = LLMService()
