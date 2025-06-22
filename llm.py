from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

def get_llm_chain():
    """Configura y devuelve la cadena de LangChain con el LLM."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
    
    prompt_template = PromptTemplate(
        input_variables=["job_text"],
        template="""
        Eres un asistente experto en extracción de datos. A partir del texto de una página web de una oferta de empleo, extrae la siguiente información y devuélvela en formato JSON válido. Si algún campo no está disponible, usa "N/A". Identifica las habilidades o requisitos técnicos mencionados.

        Campos a extraer:
        - title: Título del puesto
        - company: Nombre de la empresa
        - description: Descripción general del puesto
        - location: Ubicación del empleo (puede incluir "Remoto" o detalles)
        - salary: Salario (si está especificado, de lo contrario "Not specified")
        - date_posted: Fecha de publicación
        - job_type: Tipo de empleo (ej. Full time, Part time)
        - requirements: Lista de habilidades o requisitos (ej. ["Python", "React", "5 años de experiencia"])

        Texto de la página:
        {job_text}

        Devuelve SOLO un objeto JSON válido, sin texto adicional, comentarios ni formato markdown. Ejemplo:
        {{"title":"Ejemplo","company":"N/A","description":"N/A","location":"N/A","salary":"Not specified","date_posted":"N/A","job_type":"N/A","requirements":["N/A"]}}
        """
    )
    
    chain = prompt_template | llm | StrOutputParser()
    return chain