return [{
    json: {
      chat_id: $input.item.json.Key.split('/').pop().replace('.json', '') || "default_chat_id",
    }
  }];