const chatId = $input.all()[0].json.message.chat.id;
const messageText = $input.all()[0].json.message.text;

// Generar un user_id único
const userId = `user_${chatId}_${Date.now()}`;

// Prompt para Gemini
const prompt = `
Un usuario envió el mensaje: "${messageText}"

Extraé los datos y generá un JSON con esta estructura exacta:
{
  "name": "<Nombre o 'Usuario_${chatId}' si no se proporciona>",
  "email": "<Email o '' si no se proporciona>",
  "skills": ["<habilidad1>", "<habilidad2>", ...],
  "job_type": "<Tipo de trabajo, por ejemplo, 'Full time'>",
  "location": "<Ubicación, por ejemplo, 'Remoto'>"
}

Ejemplo de salida:
{
  "name": "Nico",
  "email": "nico@email.com",
  "skills": ["Fullstack", "C#", ".NET Core", "SQL Server", "SQL", "Entity Framework", "LINQ", "testing"],
  "job_type": "Full time",
  "location": "Remoto"
}

Asegúrate de que:
- El JSON sea válido.
- Las habilidades sean un array de strings.
- Usa valores por defecto si faltan datos (email: '', job_type: 'No especificado', location: 'No especificado').
- La salida esté envuelta en \`\`\`json\n y \n\`\`\`.
`;

return {
  json: {
    chat_id: chatId,
    user_id: userId,
    message: messageText,
    prompt: prompt,
    created_at: new Date().toISOString()
  }
};