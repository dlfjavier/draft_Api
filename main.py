from fastapi import FastAPI
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity

app = FastAPI()

@app.get("/peliculas_idioma/{Idioma}")
def peliculas_idioma(Idioma: str):
    # Cargar el DataFrame desde el archivo 'pq_prodCo.parquet'
    df_languages = pd.read_parquet('datasets/pq_languages.parquet')

    # Buscar el idioma en el DataFrame
    idioma_info = df_languages[df_languages['Languages'] == Idioma]

    if len(idioma_info) == 0:
        return "No se encontró información para el idioma especificado."

    cantidad_peliculas = idioma_info['Movies'].iloc[0]

    if cantidad_peliculas == 1:
        return f"Se produjo 1 película en el idioma {Idioma}"
    else:
        return f"Se produjeron {cantidad_peliculas} películas en el idioma {Idioma}"

@app.get("/peliculas_duracion/{Pelicula}")
def peliculas_duracion(Pelicula: str):
    df_runtime = pd.read_parquet('datasets/pq_runtime.parquet')
    
    pelicula_info = df_runtime[df_runtime['title'] == Pelicula]
    
    if not pelicula_info.empty:
        duracion = pelicula_info['runtime_min'].values[0]
        anio = pelicula_info['year'].values[0]
        return f"{Pelicula}. Duración: {int(duracion)} minutos. Año: {anio}"
    else:
        return f"No se encontró información para la película: {Pelicula}"

@app.get("/franquicia/{Franquicia}")
def franquicia(Franquicia: str):
    df_collections = pd.read_parquet('datasets/pq_collections.parquet')
    franquicia_data = df_collections[df_collections['collection'] == Franquicia]
    movies_count = franquicia_data['title'].count()
    total_revenue = franquicia_data['revenue'].sum()

    if movies_count > 0:
        average_revenue = total_revenue / movies_count
    else:
        average_revenue = 0

    total_revenueF = "{:,.2f}".format(total_revenue)
    average_revenueF = "{:,.2f}".format(average_revenue)
    return f"La franquicia {Franquicia} posee {movies_count} películas, una ganancia total de {total_revenueF} y una ganancia promedio de {average_revenueF}"

@app.get("/peliculas_pais/{Pais}")
def peliculas_pais( Pais: str ): 
    # Cargar el DataFrame desde el archivo 'pq_countries.parquet'
    df_countries = pd.read_parquet('datasets/pq_countries.parquet')

    # Buscar la fila correspondiente al país en el DataFrame
    country_row = df_countries[df_countries['countries_keys'] == Pais]

    if not country_row.empty:
        Z = country_row['countries_keys'].values[0]
        X = country_row['productions'].values[0]
        Y = country_row['countries'].values[0]
        mensaje = f"Se produjeron {X} películas en el país {Z} ({Y})"
        return mensaje
    else:
        return "País no encontrado en el DataFrame"

@app.get("/productoras_exitosas/{Productora}")
def productoras_exitosas(Productora: str):
    # Cargar el DataFrame desde el archivo 'pq_prodCo.parquet'
    df_prodCo = pd.read_parquet('datasets/pq_prodCo.parquet')

    # Filtrar el DataFrame para obtener las filas donde la columna 'companies' sea igual al valor de la productora
    filtro = df_prodCo['companies'] == Productora
    resultado = df_prodCo[filtro]

    # Verificar si se encontraron resultados para la productora
    if resultado.empty:
        print(f"No se encontraron datos para la productora '{Productora}'")
        return None
    else:
    # Obtener los valores de 'total_revenue' y 'total_movies' para la productora
        total_revenue_resultado = "{:,.2f}".format(resultado['total_revenue'].values[0])
        total_movies_resultado = resultado['total_movies'].values[0]

        return f"La productora {Productora} ha tenido un revenue de {total_revenue_resultado} y ha realizado {total_movies_resultado} películas."

@app.get("/get_director/{nombre_director}")
def get_director(nombre_director: str):
    df_mov_dir = pd.read_parquet('datasets/pq_mov_dir.parquet')

    # Filtrar el DataFrame para obtener solo las películas dirigidas por el director dado
    director_movies = df_mov_dir[df_mov_dir['director'] == nombre_director]

    if director_movies.empty:
        # Si no hay películas del director en el DataFrame, retornar mensaje apropiado
        return "No se encontraron películas dirigidas por {}".format(nombre_director)

    # Filtrar para considerar solo los registros con valores numéricos en 'revenue' y 'budget'
    valid_movies = director_movies[
        pd.to_numeric(director_movies['revenue'], errors='coerce').notna() &
        pd.to_numeric(director_movies['budget'], errors='coerce').notna()
        ]

    if valid_movies.empty:
        # Si no hay películas con valores numéricos en 'revenue' y 'budget', retornar mensaje apropiado
        return "No se encontraron películas con información de revenue y budget para {}".format(nombre_director)

    # Calcular el total_return como la división entre la suma de 'revenue' y la suma de 'budget'
    #total_return = valid_movies['revenue'].sum() / valid_movies['budget'].sum()#5.33
    total_return = valid_movies['return'].sum() #310.00
    #total_return = valid_movies['return'].sum() / len(valid_movies['return'])#10.33

    # Preparar la lista de detalles de cada película
    detalles_peliculas = []
    for index, row in director_movies.iterrows():
        pelicula = [
            row['title'],
            row['release_date'],
            '{:,.2f}'.format(row['return']),
            '{:,.2f}'.format(row['budget']) if not pd.isnull(row['budget']) else 'Sin información',
            '{:,.2f}'.format(row['revenue']) if not pd.isnull(row['revenue']) else 'Sin información'
        ]
        detalles_peliculas.append(pelicula)

    # Formatear los valores 'nan' como 'Sin información'
    detalles_peliculas_str = []
    for pelicula in detalles_peliculas:
        detalles_peliculas_str.append([val if val != 'nan' else 'Sin información' for val in pelicula])

    # Retornar la respuesta formateada
    respuesta = "{} tiene un retorno_total_director de {:,.2f}.".format(nombre_director, total_return)
    respuesta += "\n" + '\n'.join([', '.join(pelicula) for pelicula in detalles_peliculas_str])
    return respuesta


@app.get("/recomendacion/{titulo}")
def recomendacion(titulo: str):
    # Cargar el DataFrame desde el archivo pq_reccom.parquet
    df = pd.read_parquet('datasets/pq_reccom.parquet')
    tfidf = TfidfVectorizer(stop_words="english")
    df['title'] = df['title'].fillna("")

    tfidf_matrix = tfidf.fit_transform(df["title"])
    coseno_sim = linear_kernel(tfidf_matrix,tfidf_matrix)

    indices = pd.Series (df.index, index = df['title']).drop_duplicates()
    idx = indices[titulo]
    idx = min(idx, len(df)-1)
    simil = list(enumerate(coseno_sim[idx]))
    simil = sorted(simil, key= lambda x: x[1], reverse=True)
    simil = simil[1:11]
    movie_index = [df[0] for df in simil]

    lista = df['title'].iloc[movie_index].to_list()[:5]

    return {'Lista recomendada': lista}