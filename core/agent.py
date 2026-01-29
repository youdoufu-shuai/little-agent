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
        # self.history 已被移除，改为使用 session_manager

    def process_message(self, message, session_id=None):
        """
        处理来自 Plato 或 Web 的传入消息（字典）。
        预期结构: {"chat_id": "...", "text": "...", "image": "..."}
        
        :param message: 消息字典
        :param session_id: 可选的会话 ID。如果未提供，则创建一个新的或使用默认值。
        :return: 响应文本
        """
        chat_id = message.get("chat_id")
        user_text = message.get("text", "")
        image_url = message.get("image")
        db_config = message.get("db_config")
        file_config = message.get("file_config")

        # 确保会话存在
        if not session_id:
             # 如果未提供则创建新会话（或者可以由调用者处理）
             # 对于 Web 界面，通常调用者会提供 session_id 或请求创建一个。
             # 如果调用时没有 session_id（例如来自 Plato webhook），我们可能需要一种映射策略。
             # 为简单起见，如果缺失则创建一个新的。
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
            history_messages.append(msg)
        
        # 构建 LLM 消息
        # 获取活跃人格
        active_persona = self.persona_manager.get_active_persona()
        system_content = active_persona["system_prompt"] if active_persona else "你是一个智能个人助手。"
        
        if db_config:
            system_content += f"\n\n[MySQL配置信息]\nHost: {db_config.get('host')}\nPort: {db_config.get('port')}\nUser: {db_config.get('user')}\nPassword: {db_config.get('password')}\nDatabase: {db_config.get('database')}\n\n注意：上述配置是基础连接信息。\n1. 如果用户查询的是当前配置的数据库，直接使用上述所有参数。\n2. 如果用户查询的是**其他数据库**（例如 'test10'），请**保持 Host, Port, User, Password 不变**，仅将 'database' 参数修改为目标数据库名（例如 'test10'）。\n3. **严禁**为了查找数据库配置而浏览本地文件（如 list_directory, read_file），除非用户明确要求查看配置文件。直接尝试使用上述凭证连接。"

        system_prompt = {
            "role": "system", 
            "content": system_content
        }
        
        # 使用最近 20 轮对话（为工具上下文增加）
        messages = [system_prompt] + history_messages[-20:]
        
        # 工具执行循环
        max_turns = 10  # 稍微增加最大轮数以避免过早失败
        current_turn = 0
        
        while current_turn < max_turns:
            llm_response = self.llm.chat(messages, tools=TOOLS_SCHEMA)
            current_turn += 1
            
            if not llm_response:
                response_text = "抱歉，处理您的请求时遇到了错误。"
                break
                
            # 检查工具调用
            if llm_response.tool_calls:
                # 将带有工具调用的助手消息添加到历史记录/消息
                # 将 tool_calls 对象转换为字典列表以便存储
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
                
                # 添加到会话管理器
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
                
                # 添加到当前消息列表以供下一次迭代
                assistant_msg = {
                    "role": "assistant",
                    "content": llm_response.content,
                    "tool_calls": tool_calls_data
                }
                messages.append(assistant_msg)
                
                # 执行工具
                for tool_call in llm_response.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    
                    print(f"Executing tool: {func_name} with args: {func_args}")
                    
                    # 权限检查
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
                            # 标准化路径以进行比较（初步实现）
                            # 在实际应用中，使用 os.path.abspath 和 os.path.commonpath
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
                            # 对 query_mysql 的特殊处理，如果参数或上下文中提供了 host/user/pass
                            # 工具定义需要它们。
                            # 如果 LLM 根据系统提示生成它们，那也没问题。
                            tool_result = AVAILABLE_TOOLS[func_name](**func_args)
                        except Exception as e:
                            tool_result = f"Error executing tool: {str(e)}"
                    else:
                        tool_result = f"Error: Tool '{func_name}' not found."
                    
                    # 如果工具结果太长，截断以节省 token
                    if len(tool_result) > 2000:
                         tool_result_truncated = tool_result[:2000] + "\n...(Output truncated due to length)..."
                    else:
                         tool_result_truncated = tool_result

                    # 将工具结果添加到会话（存储完整结果还是截断版？截断版对 token 更安全）
                    # 对于会话历史（显示），我们可能想要完整结果，但对于 LLM 上下文，使用截断版。
                    # 但 SessionManager 存储到文件，LLM 最终会从文件读取。
                    # 因此，存储截断版本更有利于长期健康。
                    
                    self.session_manager.add_message(
                        session_id,
                        "tool",
                        tool_result_truncated,
                        tool_call_id=tool_call.id
                    )
                    
                    # 添加到消息
                    messages.append({
                        "role": "tool",
                        "content": tool_result_truncated,
                        "tool_call_id": tool_call.id
                    })
                
                current_turn += 1
            else:
                # 最终文本响应
                response_text = llm_response.content
                self.session_manager.add_message(session_id, "assistant", response_text)
                break

        if not response_text and current_turn >= max_turns:
            response_text = "抱歉，由于任务过于复杂，我停止了思考（达到最大步骤限制）。"
            self.session_manager.add_message(session_id, "assistant", response_text)

        # 4. 响应（Plato 后备）
        # self.plato.send_message(chat_id, response_text)
        
        return {
            "response": response_text,
            "session_id": session_id
        }
