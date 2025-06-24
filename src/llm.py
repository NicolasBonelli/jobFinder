from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

def get_llm_chain():
    """Configura y devuelve la cadena de LangChain con el LLM."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
    
    prompt_template = PromptTemplate(
        input_variables=["job_text"],
        template="""
        Eres un asistente experto en extracción de datos y procesamiento de texto para sistemas de inteligencia artificial.

        A partir del siguiente texto extraído de una oferta de empleo, extrae la información solicitada en formato JSON válido. Si un campo no está presente, usa "N/A".
        IMPORTANTE:
        Para el campo "requirements", convierte todos los requisitos o habilidades en etiquetas **cortas**, claras y generalizadas:
        - Usá solo **una o dos palabras por habilidad**.
        - Eliminar redundancias y descripciones largas.
        - Ejemplos:
        - "Experiencia en desarrollo backend (2+ años)" → "backend +2 años"
        - "Conocimientos sólidos en pruebas unitarias, de integración y end-to-end" → "testing"
        - "Capacidad para trabajar en equipo" → "teamwork"
        - "Manejo de base de datos relacionales como MySQL o PostgreSQL" → "SQL"
        ---
        Campos a extraer:
        - title: Título del puesto
        - company: Nombre de la empresa
        - description: Descripción general del puesto
        - location: Ubicación del empleo (puede incluir "Remoto")
        - salary: Salario si está especificado, o "Not specified"
        - date_posted: Fecha de publicación
        - job_type: Tipo de empleo (ej: Full time, Part time)
        - requirements: Lista de habilidades o requisitos clave, expresados como etiquetas cortas (ej. ["Python", "SQL", "testing", "agile"])
        ---
        Texto de la oferta:
        {job_text}

        Devuelve SOLO un objeto JSON válido, sin comentarios, texto adicional ni formato Markdown.
        Ejemplo:
        {{"title":"Ejemplo","company":"N/A","description":"N/A","location":"N/A","salary":"Not specified","date_posted":"N/A","job_type":"N/A","requirements":["Python", "SQL", "teamwork"]}}
        """
    )
    
    chain = prompt_template | llm | StrOutputParser()
    return chain