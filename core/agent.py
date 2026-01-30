import json
import datetime
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
        # self.history 已被移除，改为使用 session_manager

    def process_message(self, message, session_id=None):
        """
        处理来自 Plato 或 Web 的传入消息（字典）。
        预期结构: {"chat_id": "...", "text": "...", "image": "..."}
        
        :param message: 消息字典
        :param session_id: 可选的会话 ID。如果未提供，则创建一个新的或使用默认值。
        :return: 响应文本
        """
        # 为了兼容性保留此方法，但在内部我们可以调用流式处理并聚合结果
        # 或者为了稳定性暂时保留原样。鉴于这是一个演示项目，
        # 我们保留原样以避免破坏现有逻辑，而在下方添加新的流式方法。
        # (此处代码与之前相同，略去修改)
        chat_id = message.get("chat_id")
        user_text = message.get("text", "")
        image_url = message.get("image")
        db_config = message.get("db_config")
        file_config = message.get("file_config")

        # 确保会话存在
        if not session_id:
             session = self.session_manager.create_session(title=user_text[:20])
             session_id = session["id"]

        response_text = ""

        # 1. 视觉大脑
        if image_url:
            print(f"Processing image from {chat_id}...")
            vision_desc = self.vision.analyze_image(image_url)
            user_text += f"\n[System Note: User uploaded an image. Description: {vision_desc}]"

        # 2. 通过 Session Manager 更新历史记录
        self.session_manager.add_message(session_id, "user", user_text)

        # 3. 逻辑大脑
        print(f"Thinking for {chat_id} in session {session_id}...")
        
        # 从会话中获取历史记录
        session = self.session_manager.get_session(session_id)
        
        # 将会话消息转换为 LLM 格式
        history_messages = []
        for m in session.get("messages", []):
            msg = {"role": m["role"], "content": m["content"]}
            if "tool_calls" in m:
                msg["tool_calls"] = m["tool_calls"]
            if "tool_call_id" in m:
                msg["tool_call_id"] = m["tool_call_id"]
            if "name" in m:
                msg["name"] = m["name"]
            history_messages.append(msg)
        
        # 构建 LLM 消息
        active_persona = self.persona_manager.get_active_persona()
        base_system = active_persona["system_prompt"] if active_persona else "你是一个智能个人助手。"
        
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        system_content = f"当前时间：{current_time_str}\n{base_system}\n\n[核心指令]\n1. 收到复杂需求时，必须先输出【执行计划】，再调用工具。\n2. 能够感知当前时间，对于时间敏感的查询（如新闻、热搜），请使用当前日期进行搜索。"
        
        if db_config:
            system_content += f"\n\n[MySQL配置信息]\nHost: {db_config.get('host')}\nPort: {db_config.get('port')}\nUser: {db_config.get('user')}\nPassword: {db_config.get('password')}\nDatabase: {db_config.get('database')}\n\n注意：上述配置是基础连接信息。\n1. 如果用户查询的是当前配置的数据库，直接使用上述所有参数。\n2. 如果用户查询的是**其他数据库**（例如 'test10'），请**保持 Host, Port, User, Password 不变**，仅将 'database' 参数修改为目标数据库名（例如 'test10'）。\n3. **严禁**为了查找数据库配置而浏览本地文件（如 list_directory, read_file），除非用户明确要求查看配置文件。直接尝试使用上述凭证连接。"

        system_prompt = {
            "role": "system", 
            "content": system_content
        }
        
        tool_id_to_name = {}
        for msg in history_messages:
            if msg.get("role") == "assistant" and "tool_calls" in msg:
                for tc in msg["tool_calls"]:
                    if isinstance(tc, dict):
                        tid = tc.get("id")
                        fname = tc.get("function", {}).get("name")
                        if tid and fname:
                            tool_id_to_name[tid] = fname
            elif msg.get("role") == "tool" and ("name" not in msg or not msg["name"]):
                tid = msg.get("tool_call_id")
                if tid and tid in tool_id_to_name:
                    msg["name"] = tool_id_to_name[tid]

        start_index = len(history_messages) - 20
        if start_index < 0:
            start_index = 0
            
        while start_index > 0 and history_messages[start_index].get("role") != "user":
            start_index -= 1
            
        recent_messages = history_messages[start_index:]
        messages = [system_prompt] + recent_messages
        
        max_turns = message.get("max_steps", 10)
        current_turn = 0
        
        while current_turn < max_turns:
            llm_response = self.llm.chat(messages, tools=TOOLS_SCHEMA)
            current_turn += 1
            
            if not llm_response:
                response_text = "抱歉，处理您的请求时遇到了错误。"
                break
                
            if llm_response.tool_calls:
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
                
                assistant_msg = {
                    "role": "assistant",
                    "content": llm_response.content,
                    "tool_calls": tool_calls_data
                }
                messages.append(assistant_msg)
                
                for tool_call in llm_response.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    
                    print(f"Executing tool: {func_name} with args: {func_args}")
                    
                    permission_granted = True
                    error_msg = ""
                    
                    if file_config and func_name in ["read_file", "list_directory", "write_file", "search_files"]:
                        allow_read = file_config.get("allow_read", True)
                        allowed_paths = file_config.get("allowed_paths", [])
                        
                        target_path = func_args.get("file_path") or func_args.get("dir_path") or func_args.get("root_dir")
                        
                        if not allow_read:
                            permission_granted = False
                            error_msg = f"Error: File access is disabled by user settings. Cannot execute '{func_name}'."
                        elif allowed_paths and target_path:
                            import os
                            target_abs = os.path.abspath(target_path)
                            is_allowed = False
                            for p in allowed_paths:
                                allowed_abs = os.path.abspath(p)
                                if target_abs.startswith(allowed_abs):
                                    is_allowed = True
                                    break
                            
                            if not is_allowed:
                                permission_granted = False
                                error_msg = f"Error: Access to path '{target_path}' is denied. Allowed paths: {allowed_paths}"

                    if not permission_granted:
                        tool_result = error_msg
                    elif func_name in AVAILABLE_TOOLS:
                        try:
                            tool_result = AVAILABLE_TOOLS[func_name](**func_args)
                        except Exception as e:
                            tool_result = f"Error executing tool: {str(e)}"
                    else:
                        tool_result = f"Error: Tool '{func_name}' not found."
                    
                    if len(tool_result) > 2000:
                         tool_result_truncated = tool_result[:2000] + "\n...(Output truncated due to length)..."
                    else:
                         tool_result_truncated = tool_result

                    self.session_manager.add_message(
                        session_id,
                        "tool",
                        tool_result_truncated,
                        tool_call_id=tool_call.id,
                        name=func_name
                    )
                    
                    messages.append({
                        "role": "tool",
                        "content": tool_result_truncated,
                        "tool_call_id": tool_call.id,
                        "name": func_name
                    })
            else:
                response_text = llm_response.content
                self.session_manager.add_message(session_id, "assistant", response_text)
                break

        finish_reason = "stop"
        if current_turn >= max_turns and not response_text:
            finish_reason = "length"
            response_text = "任务执行步骤已达上限，是否继续？"
            self.session_manager.add_message(session_id, "assistant", response_text)

        return {
            "response": response_text,
            "session_id": session_id,
            "finish_reason": finish_reason
        }

    def process_message_stream(self, message, session_id=None):
        """
        Stream version of process_message.
        Yields events: 
        {"type": "content", "content": "..."}
        {"type": "tool_start", "tool": "...", "input": "..."}
        {"type": "tool_result", "tool": "...", "output": "..."}
        {"type": "meta", "session_id": "...", "finish_reason": "..."}
        """
        chat_id = message.get("chat_id")
        user_text = message.get("text", "")
        image_url = message.get("image")
        db_config = message.get("db_config")
        file_config = message.get("file_config")

        if not session_id:
             session = self.session_manager.create_session(title=user_text[:20])
             session_id = session["id"]
        
        yield {"type": "meta", "session_id": session_id}

        # 1. Vision Brain
        if image_url:
            vision_desc = self.vision.analyze_image(image_url)
            user_text += f"\n[System Note: User uploaded an image. Description: {vision_desc}]"
            yield {"type": "thought", "content": f"Analyzed image: {vision_desc}"}

        # 2. Update History
        self.session_manager.add_message(session_id, "user", user_text)

        # 3. Logic Brain setup (similar to process_message)
        session = self.session_manager.get_session(session_id)
        history_messages = []
        for m in session.get("messages", []):
            msg = {"role": m["role"], "content": m["content"]}
            if "tool_calls" in m:
                msg["tool_calls"] = m["tool_calls"]
            if "tool_call_id" in m:
                msg["tool_call_id"] = m["tool_call_id"]
            if "name" in m:
                msg["name"] = m["name"]
            history_messages.append(msg)
        
        active_persona = self.persona_manager.get_active_persona()
        base_system = active_persona["system_prompt"] if active_persona else "你是一个智能个人助手。"
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_content = f"当前时间：{current_time_str}\n{base_system}\n\n[核心指令]\n1. 收到复杂需求时，必须先输出【执行计划】，再调用工具。\n2. 能够感知当前时间，对于时间敏感的查询（如新闻、热搜），请使用当前日期进行搜索。"
        if db_config:
            system_content += f"\n\n[MySQL配置信息]\nHost: {db_config.get('host')}\nPort: {db_config.get('port')}\nUser: {db_config.get('user')}\nPassword: {db_config.get('password')}\nDatabase: {db_config.get('database')}\n\n注意：上述配置是基础连接信息。\n1. 如果用户查询的是当前配置的数据库，直接使用上述所有参数。\n2. 如果用户查询的是**其他数据库**（例如 'test10'），请**保持 Host, Port, User, Password 不变**，仅将 'database' 参数修改为目标数据库名（例如 'test10'）。\n3. **严禁**为了查找数据库配置而浏览本地文件（如 list_directory, read_file），除非用户明确要求查看配置文件。直接尝试使用上述凭证连接。"

        system_prompt = {"role": "system", "content": system_content}
        
        # Tool name fix for history
        tool_id_to_name = {}
        for msg in history_messages:
            if msg.get("role") == "assistant" and "tool_calls" in msg:
                for tc in msg["tool_calls"]:
                    if isinstance(tc, dict):
                        tid = tc.get("id")
                        fname = tc.get("function", {}).get("name")
                        if tid and fname:
                            tool_id_to_name[tid] = fname
            elif msg.get("role") == "tool" and ("name" not in msg or not msg["name"]):
                tid = msg.get("tool_call_id")
                if tid and tid in tool_id_to_name:
                    msg["name"] = tool_id_to_name[tid]

        # Slicing
        start_index = len(history_messages) - 20
        if start_index < 0: start_index = 0
        while start_index > 0 and history_messages[start_index].get("role") != "user":
            start_index -= 1
        recent_messages = history_messages[start_index:]
        messages = [system_prompt] + recent_messages
        
        max_turns = message.get("max_steps", 10)
        current_turn = 0
        
        while current_turn < max_turns:
            current_turn += 1
            stream = self.llm.chat_stream(messages, tools=TOOLS_SCHEMA)
            
            current_content = ""
            current_tool_calls = {} 
            
            # Iterate stream
            for chunk in stream:
                if not chunk: continue
                delta = chunk.choices[0].delta
                
                if delta.content:
                    current_content += delta.content
                    yield {"type": "content", "content": delta.content}
                
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in current_tool_calls:
                            current_tool_calls[idx] = {
                                "id": tc.id or "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            }
                        if tc.id:
                            current_tool_calls[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                # Prevent duplicate tool names if the stream sends the full name multiple times
                                if current_tool_calls[idx]["function"]["name"] != tc.function.name:
                                    current_tool_calls[idx]["function"]["name"] += tc.function.name
                            if tc.function.arguments:
                                current_tool_calls[idx]["function"]["arguments"] += tc.function.arguments
            
            # Stream finished for this turn
            
            if current_tool_calls:
                tool_calls_list = [current_tool_calls[i] for i in sorted(current_tool_calls.keys())]
                
                # Save assistant msg
                display_content = current_content
                if not display_content:
                     tool_names = ", ".join([t['function']['name'] for t in tool_calls_data]) if 'tool_calls_data' in locals() else "tools"
                     display_content = f"[Calling tools...]"

                self.session_manager.add_message(
                    session_id, 
                    "assistant", 
                    display_content, # Might be empty if only tool calls
                    tool_calls=tool_calls_list
                )
                
                messages.append({
                    "role": "assistant",
                    "content": current_content, # None in API but string here is safer
                    "tool_calls": tool_calls_list
                })
                
                # Execute tools
                for tc in tool_calls_list:
                    func_name = tc["function"]["name"]
                    args_str = tc["function"]["arguments"]
                    
                    yield {"type": "tool_start", "tool": func_name, "input": args_str}
                    
                    # Parse args
                    parse_error = False
                    try:
                        func_args = json.loads(args_str)
                    except json.JSONDecodeError:
                        func_args = {}
                        parse_error = True
                        error_msg = f"Failed to parse arguments for {func_name}"
                        yield {"type": "error", "content": error_msg}

                    # Permission check
                    permission_granted = True
                    if not parse_error:
                        error_msg = ""
                    
                    if not parse_error and file_config and func_name in ["read_file", "list_directory", "write_file", "search_files"]:
                        allow_read = file_config.get("allow_read", True)
                        allowed_paths = file_config.get("allowed_paths", [])
                        
                        target_path = func_args.get("file_path") or func_args.get("dir_path") or func_args.get("root_dir")
                        
                        if not allow_read:
                            permission_granted = False
                            error_msg = f"Error: File access is disabled by user settings. Cannot execute '{func_name}'."
                        elif allowed_paths and target_path:
                            import os
                            target_abs = os.path.abspath(target_path)
                            is_allowed = False
                            for p in allowed_paths:
                                allowed_abs = os.path.abspath(p)
                                if target_abs.startswith(allowed_abs):
                                    is_allowed = True
                                    break
                            
                            if not is_allowed:
                                permission_granted = False
                                error_msg = f"Error: Access to path '{target_path}' is denied. Allowed paths: {allowed_paths}"

                    if not permission_granted:
                        tool_result = error_msg
                    elif func_name in AVAILABLE_TOOLS:
                        try:
                            tool_result = AVAILABLE_TOOLS[func_name](**func_args)
                        except Exception as e:
                            tool_result = f"Error executing tool: {str(e)}"
                    else:
                        tool_result = f"Error: Tool '{func_name}' not found."

                    # Yield result
                    yield {"type": "tool_result", "tool": func_name, "output": tool_result}
                    
                    # Truncate for history
                    if len(tool_result) > 2000:
                         tool_result_truncated = tool_result[:2000] + "\n...(Output truncated due to length)..."
                    else:
                         tool_result_truncated = tool_result

                    self.session_manager.add_message(
                        session_id,
                        "tool",
                        tool_result_truncated,
                        tool_call_id=tc["id"],
                        name=func_name
                    )
                    
                    messages.append({
                        "role": "tool",
                        "content": tool_result_truncated,
                        "tool_call_id": tc["id"],
                        "name": func_name
                    })
                
                # Loop continues to next turn (LLM sees tool results)
            else:
                # No tool calls, just content. Done.
                self.session_manager.add_message(session_id, "assistant", current_content)
                yield {"type": "meta", "finish_reason": "stop"}
                break
        
        if current_turn >= max_turns:
            yield {"type": "meta", "finish_reason": "length"}
            cont_msg = "任务执行步骤已达上限，是否继续？"
            self.session_manager.add_message(session_id, "assistant", cont_msg)
            yield {"type": "content", "content": cont_msg}
