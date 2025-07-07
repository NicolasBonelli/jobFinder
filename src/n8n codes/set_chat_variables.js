return [{
    json: {
      chat_id: $node["Prepare Data for Gemini"].json.chat_id || "default_chat_id",
      user_id: $node["Prepare Data for Gemini"].json.user_id || "default_user_id"
    }
  }];