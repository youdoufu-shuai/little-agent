import json
from core.llm_client import LLMClient
from core.vision_client import VisionClient
from core.plato_client import PlatoClient
from core.session_manager import SessionManager
from core.persona_manager import PersonaManager
from core.tools import TOOLS_SCHEMA, AVAILABLE_TOOLS

class PersonalAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.vision = VisionClient()
        self.plato = PlatoClient()
        self.session_manager = SessionManager()
        self.persona_manager = PersonaManager()
        # self.history is removed in favor of session_manager

    def process_message(self, message, session_id=None):
        """
        Process an incoming message (dict) from Plato or Web.
        Structure expected: {"chat_id": "...", "text": "...", "image": "..."}
        
        :param message: Message dict
        :param session_id: Optional session ID. If not provided, creates a new one or uses a default.
        :return: Response text
        """
        chat_id = message.get("chat_id")
        user_text = message.get("text", "")
        image_url = message.get("image")
        db_config = message.get("db_config")

        # Ensure session exists
        if not session_id:
             # Create new session if none provided (or could be handled by caller)
             # For web interface, usually the caller will provide session_id or ask to create one.
             # If called without session_id (e.g. from Plato webhook), we might need a mapping strategy.
             # For simplicity, we'll create a new one if missing.
             session = self.session_manager.create_session(title=user_text[:20])
             session_id = session["id"]

        response_text = ""

        # 1. Vision Brain
        if image_url:
            print(f"Processing image from {chat_id}...")
            vision_desc = self.vision.analyze_image(image_url)
            user_text += f"\n[System Note: User uploaded an image. Description: {vision_desc}]"

        # 2. Update History via Session Manager
        self.session_manager.add_message(session_id, "user", user_text)

        # 3. Logic Brain
        print(f"Thinking for {chat_id} in session {session_id}...")
        
        # Retrieve history from session
        session = self.session_manager.get_session(session_id)
        
        # Convert session messages to LLM format
        history_messages = []
        for m in session.get("messages", []):
            msg = {"role": m["role"], "content": m["content"]}
            if "tool_calls" in m:
                msg["tool_calls"] = m["tool_calls"]
            if "tool_call_id" in m:
                msg["tool_call_id"] = m["tool_call_id"]
            history_messages.append(msg)
        
        # Construct messages for LLM
        # Get active persona
        active_persona = self.persona_manager.get_active_persona()
        system_content = active_persona["system_prompt"] if active_persona else "你是一个智能个人助手。"
        
        if db_config:
            system_content += f"\n\n[MySQL配置信息]\nHost: {db_config.get('host')}\nPort: {db_config.get('port')}\nUser: {db_config.get('user')}\nPassword: {db_config.get('password')}\nDatabase: {db_config.get('database')}\n\n注意：上述配置是基础连接信息。\n1. 如果用户查询的是当前配置的数据库，直接使用上述所有参数。\n2. 如果用户查询的是**其他数据库**（例如 'test10'），请**保持 Host, Port, User, Password 不变**，仅将 'database' 参数修改为目标数据库名（例如 'test10'）。\n3. **严禁**为了查找数据库配置而浏览本地文件（如 list_directory, read_file），除非用户明确要求查看配置文件。直接尝试使用上述凭证连接。"

        system_prompt = {
            "role": "system", 
            "content": system_content
        }
        
        # Use last 20 turns (increased for tool context)
        messages = [system_prompt] + history_messages[-20:]
        
        # Tool execution loop
        max_turns = 10  # Increase max turns slightly to avoid premature failure
        current_turn = 0
        
        while current_turn < max_turns:
            llm_response = self.llm.chat(messages, tools=TOOLS_SCHEMA)
            
            if not llm_response:
                response_text = "抱歉，处理您的请求时遇到了错误。"
                break
                
            # Check for tool calls
            if llm_response.tool_calls:
                # Add assistant message with tool calls to history/messages
                # Convert tool_calls object to list of dicts for storage
                tool_calls_data = []
                for tc in llm_response.tool_calls:
                    tool_calls_data.append({
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })
                
                # Add to session manager
                display_content = llm_response.content
                if not display_content:
                     tool_names = ", ".join([t['function']['name'] for t in tool_calls_data])
                     display_content = f"[正在调用工具: {tool_names}...]"

                self.session_manager.add_message(
                    session_id, 
                    "assistant", 
                    display_content, 
                    tool_calls=tool_calls_data
                )
                
                # Add to current messages list for next iteration
                assistant_msg = {
                    "role": "assistant",
                    "content": llm_response.content,
                    "tool_calls": tool_calls_data
                }
                messages.append(assistant_msg)
                
                # Execute tools
                for tool_call in llm_response.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    
                    print(f"Executing tool: {func_name} with args: {func_args}")
                    
                    if func_name in AVAILABLE_TOOLS:
                        try:
                            # Special handling for query_mysql if host/user/pass provided in args OR from context
                            # The tool definition requires them.
                            # If the LLM generates them based on system prompt, it's fine.
                            tool_result = AVAILABLE_TOOLS[func_name](**func_args)
                        except Exception as e:
                            tool_result = f"Error executing tool: {str(e)}"
                    else:
                        tool_result = f"Error: Tool '{func_name}' not found."
                    
                    # Truncate tool result if too long to save tokens
                    if len(tool_result) > 2000:
                         tool_result_truncated = tool_result[:2000] + "\n...(Output truncated due to length)..."
                    else:
                         tool_result_truncated = tool_result

                    # Add tool result to session (store full result or truncated? Truncated is safer for tokens)
                    # For session history (display), we might want full result but for LLM context, truncated.
                    # But SessionManager stores to file, LLM reads from file eventually.
                    # So storing truncated version is better for long-term health.
                    
                    self.session_manager.add_message(
                        session_id,
                        "tool",
                        tool_result_truncated,
                        tool_call_id=tool_call.id
                    )
                    
                    # Add to messages
                    messages.append({
                        "role": "tool",
                        "content": tool_result_truncated,
                        "tool_call_id": tool_call.id
                    })
                
                current_turn += 1
            else:
                # Final text response
                response_text = llm_response.content
                self.session_manager.add_message(session_id, "assistant", response_text)
                break

        if not response_text and current_turn >= max_turns:
            response_text = "抱歉，由于任务过于复杂，我停止了思考（达到最大步骤限制）。"
            self.session_manager.add_message(session_id, "assistant", response_text)

        # 4. Respond (Plato fallback)
        # self.plato.send_message(chat_id, response_text)
        
        return {
            "response": response_text,
            "session_id": session_id
        }
