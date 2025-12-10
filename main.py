# Archivo principal que ejecuta todo
import os
import sys
from dotenv import load_dotenv
# Importamos la nueva función (asegúrate de que el nombre del archivo coincida)
# Si sobrescribiste downloader.py, mantén "from src.downloader..."
# Si creaste src/media_processor.py, cambia el import.
from src.downloader import procesar_video_local 
from src.analyzer import analizar_con_gemini
from src.extractor import capturar_frames
from src.generator import generar_pdf

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    if not API_KEY:
        print("❌ Error: Falta GEMINI_API_KEY en .env")
        return

    # Lógica para detectar argumento o pedir input
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        print("\n--- GENERADOR DE GUÍAS PARA VIDEO LOCAL ---")
        # Tip: En VS Code puedes arrastrar el archivo a la terminal para pegar la ruta
        input_file = input("Arrastra tu vídeo aquí o escribe la ruta absoluta: ").strip().strip("'").strip('"')
    
    # Validar que existe antes de empezar
    if not os.path.exists(input_file):
        print(f"❌ El archivo no existe: {input_file}")
        print("Consejo: En DevContainers, asegúrate de que el video está dentro de la carpeta del proyecto.")
        return

    base_output = "output"
    os.makedirs(base_output, exist_ok=True)
    
    try:
        # 1. Procesamiento Local
        # Notarás que la función ahora se llama procesar_video_local
        video_path, audio_path, frames_folder, video_title = procesar_video_local(input_file, base_output)
        
        print(f"📘 Título: {video_title}")
        
        # 2. Análisis IA (Esto no cambia nada, la IA no sabe si el video es de YouTube o local)
        guia_data = analizar_con_gemini(audio_path, frames_folder, API_KEY)
        
        # 3. Frames finales
        guia_con_fotos = capturar_frames(guia_data, video_path, base_output)
        
        # 4. Generar PDF
        output_pdf = os.path.join(base_output, f"{video_title.replace(' ', '_')}_Guia.pdf")
        generar_pdf(guia_con_fotos, output_pdf, video_title)
        
    except Exception as e:
        print(f"\n❌ Proceso fallido: {e}")

if __name__ == "__main__":
    main()