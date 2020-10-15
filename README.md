# Práctica 1: Web scraping

## Descripción
Un dataset sobre **los pisos que están en alquiler en barcelona**, aunque el scraper está diseñado para poder recuperar otra ciudad cambiando la variable **city_name = 'barcelona'**

## Miembro del equipo
- Daria Gracheva 
- Zechao Jin

## Cómo ejecutar
1. Instala librería con: **pip install -r requirements.txt**
2. Ejecuta el comando **python main.py**

## Estructura del programa
- **get_pages_url_worker** se encarga de recuperar url de cada piso y guarda en la cola **pages_url_queue** para ser tratado
- Unos workers **page_resolve_wioker** encargan de traer datos de cada página, el resultado se guarda en otra cola **result_queue**
- **write_file_worker** se encarga de escribir los datos en el archivo dataset.csv
En la siguiente figura muestra el flujo de nuestro web scraper concurrente
![flujo](img/flujo.png)