# Módulo para tomar un vídeo local y extraer audio e imágenes para procesamiento posterior.
import os
import subprocess
import glob
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def obtener_metadata(video_path):
    """Obtiene duración y título (si existe) del archivo local."""
    meta = {'duration': 600.0, 'title': Path(video_path).stem} # Título por defecto: nombre del archivo
    
    try:
        # 1. Obtener Duración
        cmd_dur = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', video_path
        ]
        res_dur = subprocess.run(cmd_dur, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        meta['duration'] = float(res_dur.stdout)

        # 2. Intentar obtener Título incrustado (metadata)
        cmd_title = [
            'ffprobe', '-v', 'error', '-show_entries', 'format_tags=title', 
            '-of', 'default=noprint_wrappers=1:nokey=1', video_path
        ]
        res_title = subprocess.run(cmd_title, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res_title.stdout.strip():
            meta['title'] = res_title.stdout.strip().replace("TAG:title=", "")
            
    except Exception as e:
        print(f"⚠️  Advertencia leyendo metadatos: {e}")
    
    return meta

def procesar_video_local(input_path, output_folder):
    """
    Toma un video local y genera los recursos (mp3 + frames) para la IA.
    """
    if not os.path.exists(input_path):
        print(f"❌ Error: El archivo '{input_path}' no existe.")
        sys.exit(1)

    print(f"📂 Procesando archivo local: {input_path}")
    
    # Preparamos carpetas
    video_working_path = os.path.join(output_folder, "video_work.mp4")
    audio_path = os.path.join(output_folder, "audio.mp3")
    frames_folder = os.path.join(output_folder, "ia_frames")
    
    # Limpieza
    if os.path.exists(audio_path): os.remove(audio_path)
    if not os.path.exists(frames_folder): os.makedirs(frames_folder)
    for f in glob.glob(f"{frames_folder}/*.jpg"): os.remove(f)

    # 1. Copiar video a carpeta de trabajo (opcional, pero más seguro para trabajar)
    # Si el video es enorme, podríamos usar symlink, pero copiar evita problemas de permisos.
    print("   📋 Copiando video al espacio de trabajo...")
    shutil.copy2(input_path, video_working_path)

    # 2. Analizar Metadata
    print("   ⏱️  Analizando archivo...")
    metadata = obtener_metadata(video_working_path)
    duracion = metadata['duration']
    titulo = metadata['title']
    
    # 3. Calcular Muestreo (Lectura del .env)
    try:
        MAX_IMAGENES = int(os.getenv("MAX_IMAGENES", "150"))
        INTERVALO_DESEADO = float(os.getenv("INTERVALO_DESEADO", "2.0"))
    except ValueError:
        MAX_IMAGENES = 150
        INTERVALO_DESEADO = 2.0
    
    if (duracion / INTERVALO_DESEADO) > MAX_IMAGENES:
        intervalo_final = duracion / MAX_IMAGENES
        print(f"      ℹ️ Video largo ({duracion:.0f}s). Ajustando a 1 foto cada {intervalo_final:.2f}s.")
    else:
        intervalo_final = INTERVALO_DESEADO
        print(f"      ✅ Densidad máxima: 1 foto cada {intervalo_final}s.")

    # 4. Extraer Audio
    print("   🎵 Extrayendo audio...")
    try:
        cmd_audio = ['ffmpeg', '-i', video_working_path, '-vn', '-b:a', '32k', audio_path, '-y']
        subprocess.run(cmd_audio, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error FFmpeg Audio: {e}")
        sys.exit(1)
    
    # 5. Extraer Capturas
    print("   📸 Extrayendo capturas...")
    try:
        cmd_frames = [
            'ffmpeg', '-i', video_working_path, 
            '-vf', f'fps=1/{intervalo_final}', 
            '-q:v', '2', 
            f'{frames_folder}/frame_%03d.jpg', '-y'
        ]
        subprocess.run(cmd_frames, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("❌ Error extrayendo imágenes.")
        sys.exit(1)
    
    return video_working_path, audio_path, frames_folder, titulo