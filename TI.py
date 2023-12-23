from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import threading
import base64
import io

import numpy as np
from flask_cors import CORS

app = Flask(__name__, static_url_path='/static')
CORS(app)



@app.route('/')
def index():
    return render_template('index.html')

def save_image(text):
    # Tamaño de la imagen
    image_width = 300
    image_height = 100

    # Crea una imagen en blanco
    image = Image.new('RGB', (image_width, image_height), color='white')
    draw = ImageDraw.Draw(image)

    # Calcula el tamaño de la fuente para que se ajuste a la imagen
    font_size = 1
    font = ImageFont.truetype("arial.ttf", font_size)  # Cambia "arial.ttf" según la fuente que desees usar
    text_width, text_height = draw.textsize(text, font=font)
    while text_width < image_width and text_height < image_height:
        font_size += 1
        font = ImageFont.truetype("arial.ttf", font_size)
        text_width, text_height = draw.textsize(text, font=font)

    # Dibuja el texto en la imagen
    draw.text(((image_width - text_width) // 2, (image_height - text_height) // 2), text, font=font, fill='black')

    # Guarda la imagen sobrescribiendo el archivo existente
    image_path = os.path.join('guardar_imagen', 'palabra_aleatoria.png')
    image.save(image_path)



def calcular_porcentaje_coincidencia(imagen1, imagen2, umbral=0.95):
    # Convierte las imágenes a matrices NumPy
    np_imagen1 = np.array(imagen1.convert("L"))
    np_imagen2 = np.array(imagen2.convert("L"))

    # Crea una matriz booleana indicando píxeles coincidentes
    coincidentes = np_imagen1 == np_imagen2

    # Calcula el porcentaje de coincidencia basado en el umbral
    porcentaje_coincidencia = (np.sum(coincidentes) / coincidentes.size)

    # Aplica el umbral
    porcentaje_coincidencia = 100.0 * (porcentaje_coincidencia > umbral)

    # Redondea el porcentaje a dos decimales
    porcentaje_coincidencia = round(porcentaje_coincidencia, 2)

    return porcentaje_coincidencia



def guardar_imagen(image_data):
    # Decodifica los datos base64 y crea una imagen
    image = Image.open(io.BytesIO(base64.b64decode(image_data.split(',')[1])))

    # Crea una nueva imagen con fondo blanco y copia el trazo
    nueva_imagen = Image.new('RGB', (300, 100), 'white')  # Puedes ajustar el tamaño aquí
    draw = ImageDraw.Draw(nueva_imagen)
    draw.bitmap((0, 0), image, 'black')

    # Guarda la nueva imagen con fondo blanco con el nombre deseado
    image_path = os.path.join('guardar_imagen', 'palabra_aleatoria.png')
    nueva_imagen.save(image_path)


@app.route('/guardar_imagen', methods=['POST'])
def guardar_imagen_route():
    data = request.form
    if 'image_data' not in data:
        return jsonify({'error': 'Datos incompletos para guardar la imagen'}), 400

    image_data = data['image_data']

    # Utiliza threading para evitar bloquear el servidor Flask
    thread = threading.Thread(target=guardar_imagen, args=(image_data,))
    thread.start()

    return jsonify({'success': True, 'filename': 'palabra_aleatoria.png'})




@app.route('/obtener_imagen', methods=['GET'])
def obtener_imagen():
    filename = 'palabra_aleatoria.png'
    return send_from_directory('guardar_imagen', filename)





# Nuevo endpoint para manejar la imagen del trazo
@app.route('/guardar_trazo', methods=['POST'])
def guardar_trazo():
    # Obtiene los datos de la imagen del trazo desde la solicitud
    trazo_data = request.form['trazo_data']

    # Decodifica los datos base64 y crea una imagen
    image = Image.open(io.BytesIO(base64.b64decode(trazo_data.split(',')[1])))

    # Crea una nueva imagen con fondo blanco y copia el trazo
    nueva_imagen = Image.new('RGB', (300, 100), 'white')  # Puedes ajustar el tamaño aquí
    draw = ImageDraw.Draw(nueva_imagen)
    draw.bitmap((0, 0), image, 'black')

    # Guarda la nueva imagen con fondo blanco
    image_path = os.path.join('guardar_trazo', 'trazo.png')
    nueva_imagen.save(image_path)

    # Puedes procesar la imagen aquí o devolver una respuesta según sea necesario
    return jsonify({'mensaje': 'Imagen del trazo recibida exitosamente'})


# Nuevo endpoint para comparar las imágenes y mostrar el porcentaje de acierto
@app.route('/comparar_imagenes', methods=['POST'])
def comparar_imagenes():
    # Obtiene el nombre de la palabra actual desde la solicitud
    data = request.get_json()
    if 'text' not in data:
        return jsonify({'error': 'No se proporcionó el texto'}), 400

    text = data['text']
    imagen_guardada_path = os.path.join('guardar_imagen', 'palabra_aleatoria.png')
    trazo_path = os.path.join('guardar_trazo', 'trazo.png')

    # Verifica la existencia del trazo
    if not os.path.exists(trazo_path):
        return jsonify({'error': 'No hay un trazo para calificar'}), 400

    # Verifica la existencia de la imagen guardada
    if not os.path.exists(imagen_guardada_path):
        return jsonify({'error': 'No se encontró la imagen para la palabra aleatoria'}), 404

    try:
        # Abre las imágenes con Pillow y las convierte a matrices NumPy
        imagen_guardada = np.array(Image.open(imagen_guardada_path).convert("L"))
        trazo = np.array(Image.open(trazo_path).convert("L"))

        # Verifica si las dimensiones de las imágenes coinciden
        if imagen_guardada.shape != trazo.shape:
            return jsonify({'error': 'Las dimensiones de las imágenes no coinciden'}), 400

        # Calcula el número total de píxeles
        total_píxeles = imagen_guardada.size

        # Calcula el número de píxeles coincidentes
        píxeles_coincidentes = np.sum(imagen_guardada == trazo)

        # Verifica si no hay píxeles coincidentes
        if píxeles_coincidentes == 0:
            return jsonify({'error': 'No hay píxeles coincidentes para calcular el porcentaje de acierto'}), 400

        # Calcula el porcentaje de acierto basándose en píxeles coincidentes
        porcentaje_acierto = (píxeles_coincidentes / total_píxeles) * 100.0

        # Limita el porcentaje a un rango entre 0% y 100%
        porcentaje_acierto = max(0, min(100, porcentaje_acierto))

        # Redondea el porcentaje a dos decimales
        porcentaje_acierto = round(porcentaje_acierto, 2)

        # Muestra el porcentaje de acierto en un cuadro de diálogo
        return jsonify({'success': True, 'porcentaje_acierto': porcentaje_acierto}), 200
    except Exception as e:
        print(f'Error en la función comparar_imagenes: {str(e)}')
        return jsonify({'error': f'Error en la función comparar_imagenes: {str(e)}'}), 500




if __name__ == '__main__':
    import os

    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8000))

    gunicorn_command = f"gunicorn -w 4 -b {host}:{port} TI:app"
    os.system(gunicorn_command)
