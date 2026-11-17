
from flask import Flask, render_template, request, redirect, url_for, session
import unicodedata

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse


app = Flask(__name__)
app.secret_key = 'clave-python-http'


# EJERCICIO 1
def es_palindromo(texto):

    texto = texto.lower()

    texto = unicodedata.normalize('NFD', texto)

    texto = ''.join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != 'Mn'
    )

    texto = ''.join(
        caracter for caracter in texto
        if caracter.isalnum()
    )

    return texto == texto[::-1]


# EJERCICIO 2
def comparar_numeros(numero1, numero2):

    if numero1 > numero2:
        return f'El número mayor es {numero1:g}.'

    elif numero2 > numero1:
        return f'El número mayor es {numero2:g}.'

    else:
        return 'Los dos números son iguales.'


# EJERCICIO 3
def obtener_vocales(frase):

    vocales = []

    for caracter in frase.lower():

        caracter_normalizado = unicodedata.normalize('NFD', caracter)[0]

        if caracter_normalizado in 'aeiou' and caracter_normalizado not in vocales:
            vocales.append(caracter_normalizado)

    return vocales


# EJERCICIO 4
def contar_vocales(frase):

    vocales = {'a': 0, 'e': 0, 'i': 0, 'o': 0, 'u': 0}

    for caracter in frase.lower():

        caracter_normalizado = unicodedata.normalize('NFD', caracter)[0]

        if caracter_normalizado in vocales:
            vocales[caracter_normalizado] += 1

    return vocales


# FUNCIÓN PARA REALIZAR SOLICITUDES HTTP
def consultar_url(url):

    try:

        direccion = urlparse(url)

        if direccion.scheme not in ('http', 'https') or not direccion.netloc:

            return {
                'error': 'Introduce una URL válida que comience con http:// o https://',
                'estado_peticion': 'Error'
            }

        solicitud = Request(
            url,
            headers={'User-Agent': 'Python-HTTP-Laboratorio'}
        )

        with urlopen(solicitud, timeout=10) as respuesta:

            contenido = respuesta.read(1000000).decode(
                respuesta.headers.get_content_charset() or 'utf-8',
                errors='replace'
            )

            cabeceras = dict(respuesta.headers.items())

            return {
                'contenido': contenido,
                'cabeceras': cabeceras,
                'codigo': respuesta.status,
                'estado': respuesta.reason,
                'estado_peticion': 'Completada'
            }

    except HTTPError as error:

        contenido = error.read(1000000).decode(
            error.headers.get_content_charset() or 'utf-8',
            errors='replace'
        )

        return {
            'contenido': contenido,
            'cabeceras': dict(error.headers.items()),
            'codigo': error.code,
            'estado': error.reason,
            'estado_peticion': 'Completada con error HTTP'
        }

    except (URLError, TimeoutError, ValueError, OSError) as error:

        return {
            'error': f'No se pudo completar la solicitud: {error}',
            'estado_peticion': 'Error'
        }


# RUTA PRINCIPAL
@app.route('/', methods=['GET', 'POST'])
def inicio():

    resultado = None
    palabra = ''

    resultado_comparacion = None

    resultado_vocales = None
    frase_vocales = ''

    resultado_conteo = None
    frase_conteo = ''

    ejercicio_activo = None

    if request.method == 'POST':

        if 'palabra' in request.form:

            ejercicio_activo = 1

            palabra = request.form.get('palabra', '').strip()

            if palabra:

                if es_palindromo(palabra):
                    resultado = '¡Es un palíndromo!'
                else:
                    resultado = 'No es un palíndromo.'

            else:
                resultado = 'Introduce una palabra o frase.'

        elif 'numero1' in request.form:

            ejercicio_activo = 2

            try:

                numero1 = float(request.form.get('numero1'))
                numero2 = float(request.form.get('numero2'))

                resultado_comparacion = comparar_numeros(numero1, numero2)

            except (ValueError, TypeError):

                resultado_comparacion = 'Introduce valores numéricos válidos.'

        elif 'frase_vocales' in request.form:

            ejercicio_activo = 3

            frase_vocales = request.form.get('frase_vocales', '').strip()

            if frase_vocales:

                vocales = obtener_vocales(frase_vocales)

                if vocales:
                    resultado_vocales = ', '.join(vocales)

                else:
                    resultado_vocales = 'No se encontraron vocales.'

            else:
                resultado_vocales = 'Introduce una frase.'

        elif 'frase_conteo' in request.form:

            ejercicio_activo = 4

            frase_conteo = request.form.get('frase_conteo', '').strip()

            if frase_conteo:

                resultado_conteo = contar_vocales(frase_conteo)

            else:
                resultado_conteo = 'Introduce una frase.'

        # Guardar temporalmente los resultados
        session['resultados_ejercicios'] = {
            'resultado': resultado,
            'palabra': palabra,
            'resultado_comparacion': resultado_comparacion,
            'resultado_vocales': resultado_vocales,
            'frase_vocales': frase_vocales,
            'resultado_conteo': resultado_conteo,
            'frase_conteo': frase_conteo,
            'ejercicio_activo': ejercicio_activo
        }

        return redirect(url_for('inicio'))

    # Recuperar los resultados una sola vez
    resultados = session.pop('resultados_ejercicios', {})

    # Enviar los resultados a la plantilla HTML
    return render_template(
        'index.html',
        resultado=resultados.get('resultado'),
        palabra=resultados.get('palabra', ''),
        resultado_comparacion=resultados.get('resultado_comparacion'),
        resultado_vocales=resultados.get('resultado_vocales'),
        frase_vocales=resultados.get('frase_vocales', ''),
        resultado_conteo=resultados.get('resultado_conteo'),
        frase_conteo=resultados.get('frase_conteo', ''),
        ejercicio_activo=resultados.get('ejercicio_activo'),
        url=request.url_root,
        respuesta_http=None
    )


# RUTA DE EXPLORADOR HTTP
@app.route('/explorador', methods=['GET', 'POST'])
def explorador():

    url = request.url_root
    respuesta = None

    if request.method == 'POST':

        url = request.form.get('url', '').strip()

        if url:
            respuesta = consultar_url(url)

        # Guardar temporalmente la respuesta HTTP
        session['respuesta_http'] = respuesta
        session['url_consultada'] = url

        return redirect(url_for('explorador'))

    # Recuperar la respuesta una sola vez
    respuesta = session.pop('respuesta_http', None)

    url = session.pop('url_consultada', request.url_root)

    # Enviar los resultados a la plantilla HTML
    return render_template(
        'index.html',
        resultado=None,
        palabra='',
        resultado_comparacion=None,
        resultado_vocales=None,
        frase_vocales='',
        resultado_conteo=None,
        frase_conteo='',
        ejercicio_activo=None,
        url=url,
        respuesta_http=respuesta
    )


# INICIAR APLICACIÓN
if __name__ == '__main__':
    app.run()
