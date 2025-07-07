let jsonData;

try {
  // Ahora los datos están directamente en json.data
  jsonData = $input.item.json.data;
  
  if (!jsonData) {
    throw new Error("No se encontraron datos en json.data");
  }
  
} catch (error) {
  return {
    json: {
      error: `Error al acceder a los datos: ${error.message}`,
      debug: {
        hasJson: !!$input.item.json,
        jsonKeys: $input.item.json ? Object.keys($input.item.json) : null,
        fullJson: $input.item.json
      }
    }
  };
}

// Extraer el chatId desde el nombre del archivo
// Ahora intentamos obtenerlo de diferentes lugares posibles
const fileName = $input.item.binary?.data?.fileName || 
                $input.item.json?.fileName ||
                '';

// Extraer el chatId desde el nombre del archivo
const fileKey = $json.Key || $json.key || $json.fileName || '';
const chatId = fileKey.split('/').pop().replace('.json', '');

// Crear el prompt
const prompt = `
Sos un asistente de oportunidades laborales.

A continuación, te paso una lista de empleos que matchean con el perfil de un usuario. Estos trabajos fueron seleccionados automáticamente por un sistema de matching basado en habilidades, requisitos y puntuación de similitud.

Tu tarea es:
1. Leer todas las ofertas.
2. Seleccionar las más destacadas (hasta 3 o 4 si hay muchas).
3. Escribir un mensaje personalizado para el usuario como si se lo enviaras por Telegram.
4. El mensaje debe ser cálido, claro y directo, por ejemplo: "¡Hola! Estas son algunas oportunidades ideales para vos...".

No devuelvas JSON ni Markdown. Respondé solo con el texto final del mensaje.

---
Ofertas de trabajo:
${JSON.stringify(jsonData, null, 2)}
---
`;

return {
  json: {
    chat_id: chatId,
    prompt: prompt,
    created_at: new Date().toISOString()
  }
};