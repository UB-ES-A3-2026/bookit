# Contracte de l'API de cerca del catàleg

Contracte entre el backend i el frontend per a la cerca pública de llibres
(US4-T3 i US4-T6).

## Cercar llibres

`GET /api/cataleg/llibres/?q=<text>&page=<número>`

L'endpoint és públic i no requereix autenticació.

### Paràmetres

| Paràmetre | Obligatori | Descripció |
|---|---:|---|
| `q` | Sí | Text de cerca. Es compara sense distingir majúscules amb el títol, l'autor o l'ISBN. Els espais inicials i finals s'ignoren. |
| `page` | No | Número de pàgina, començant per `1`. Cada pàgina conté 10 resultats. |

Si `q` falta o només conté espais, la resposta és correcta però no conté
resultats.

La cerca no modifica les dades i retorna els resultats ordenats pel títol i,
en cas d'empat, per l'identificador del llibre.

### Resposta amb resultats

**HTTP 200**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "titol": "La plaça del Diamant",
      "autor": "Mercè Rodoreda",
      "isbn": "9788429740011",
      "portada": "https://covers.openlibrary.org/b/isbn/9788429740011-L.jpg",
      "disponible": true,
      "mitjana_valoracions": 4.5,
      "nombre_valoracions": 2
    }
  ]
}
```

### Camps d'un resultat

| Camp | Tipus | Descripció |
|---|---|---|
| `id` | enter | Identificador del llibre. |
| `titol` | text | Títol del llibre. |
| `autor` | text | Autor o autors del llibre. |
| `isbn` | text | ISBN del llibre. |
| `portada` | text | URL de la portada; és una cadena buida si no n'hi ha. |
| `disponible` | booleà | `true` si alguna biblioteca té almenys un exemplar disponible; `false` altrament. |
| `mitjana_valoracions` | decimal o `null` | Mitjana de les puntuacions, de `1` a `5`; `null` si el llibre no té valoracions. |
| `nombre_valoracions` | enter | Nombre de valoracions del llibre. |

### Paginació

Quan hi ha més d'una pàgina:

```json
{
  "count": 25,
  "next": "http://localhost:8000/api/cataleg/llibres/?q=historia&page=2",
  "previous": null,
  "results": []
}
```

`next` i `previous` són URLs absolutes o `null`. El frontend pot demanar la
pàgina següent utilitzant la URL retornada o el paràmetre `page`.

### Sense resultats

**HTTP 200**

```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

El frontend mostra el missatge següent quan `results` és buit:

> No s'ha trobat el llibre cercat, assegura't que l'informació introduïda sigui correcta

