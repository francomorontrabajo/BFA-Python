# BFA - PYTHON API

## DOCKER

> [!WARNING]  
> Asegúrate de que los puertos 30303 y 8545 (para el nodo) y 8000 (para la API)estén libres.

## Levantar los contenedores:

* Construye las imágenes de bfa y api.
* Levanta los contenedores y los deja corriendo en background.
* Monta volumen para persistir datos del nodo de BFA.

```sh
    docker-compose up -d --build   
```

# Ver logs de los contenedores

* Para monitorear la salida de los contenedores en tiempo real:

    * Para monitorear la salida de los contenedores en tiempo real:
        ```sh
            docker compose logs -f   
        ```
    * Para ver los logs de un contenedor específico:
        ```sh
            docker-compose logs -f bfa
            docker-compose logs -f api  
        ```

# Detener los contenedores

* Detiene los contenedores sin eliminar los volúmenes ni la configuración:

```sh
    docker compose stop  
```

# Eliminar los contenedores

* Detiene los contenedores y elimina todos los recursos asociados a docker-compose (Excepto el volúmen asociado al nodo de BFA)

```sh
    docker compose down  
```