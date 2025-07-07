// 1. Obtener la respuesta de Gemini (manejar errores si no existe)

let geminiResponse = $input.all()[0].json?.candidates?.[0]?.content?.parts?.[0]?.text;


// 2. Obtener datos del nodo anterior (Prepare Data for Gemini)
const previousNodeData = $input.all()[1]?.json ;  
const chatId = previousNodeData.chat_id ;  // Valor por defecto
const userId = previousNodeData.user_id;

// 3. Limpiar y validar el JSON
let jsonContent = geminiResponse.replace(/```json\n|\n```/g, '').trim();



const fileName = `users/${chatId}.json`;

return [{
  json: {
    userId: userId,
    chat_id: chatId,
    json_content: jsonContent,
    file_name: fileName
  }
}];