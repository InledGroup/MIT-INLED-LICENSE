import os
import json
import base64
import urllib.request
import urllib.error

# Configuración desde variables de entorno
TOKEN = os.environ.get('GITHUB_TOKEN')
ORG_NAME = os.environ.get('GITHUB_ORG')
LICENSE_PATH = 'LICENSE'  # Archivo local maestro

def github_request(url, method='GET', data=None):
    """Realiza peticiones a la API de GitHub usando urllib."""
    headers = {
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Python-License-Updater'
    }
    req = urllib.request.Request(url, headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode('utf-8')
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode()), response.info()
    except urllib.error.HTTPError as e:
        if e.code == 404 and method == 'GET':
            return None, None
        body = e.read().decode()
        print(f"Error en {url}: {e.code} - {e.reason}\nDetalle: {body}")
        return None, None
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return None, None

def update_repo_license(owner, repo_name, new_content):
    """Crea o actualiza el archivo LICENSE en un repositorio de la organización."""
    url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/LICENSE"
    
    # 1. Intentar obtener el archivo actual (para el SHA si existe)
    current_file, _ = github_request(url)
    sha = current_file['sha'] if current_file else None
    
    # 2. Preparar el payload
    payload = {
        "message": "Update LICENSE to Inled Group Standard",
        "content": base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
    }
    if sha:
        payload["sha"] = sha

    # 3. Enviar la actualización (PUT)
    result, _ = github_request(url, method='PUT', data=payload)
    if result:
        print(f"✅ [{repo_name}] Licencia {'actualizada' if sha else 'creada'} correctamente.")
    else:
        print(f"❌ [{repo_name}] Error al intentar procesar el repositorio.")

def main():
    if not TOKEN or not ORG_NAME:
        print("Error: Debes configurar GITHUB_TOKEN y GITHUB_ORG en tu terminal.")
        print("Ejemplo: export GITHUB_TOKEN='tu_token' && export GITHUB_ORG='inled-group'")
        return

    # Leer licencia local
    try:
        with open(LICENSE_PATH, 'r') as f:
            master_license = f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{LICENSE_PATH}' en este directorio.")
        return

    print(f"🚀 Iniciando actualización masiva para la organización: {ORG_NAME}...")
    
    page = 1
    processed_count = 0
    
    while True:
        # Listar repositorios de la organización
        repos_url = f"https://api.github.com/orgs/{ORG_NAME}/repos?per_page=100&page={page}"
        repos, _ = github_request(repos_url)
        
        if not repos or len(repos) == 0:
            break
            
        for repo in repos:
            # Ignorar forks si lo deseas (recomendado)
            if repo['fork']:
                print(f"⏭️  [{repo['name']}] Omitido (es un fork).")
                continue
                
            update_repo_license(ORG_NAME, repo['name'], master_license)
            processed_count += 1
            
        page += 1

    print(f"\n✨ Tarea finalizada para la organización {ORG_NAME}.")
    print(f"📦 Total de repositorios procesados: {processed_count}")

if __name__ == "__main__":
    main()
