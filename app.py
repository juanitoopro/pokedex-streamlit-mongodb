import streamlit as st
from mongo_pokedex import (
    insert_many_from_pokeapi,
    search_pokemons,
    update_pokemon,
    delete_one_by_name,
    delete_many_by_type,
    drop_collection,
    drop_database
)

st.set_page_config(page_title="Pokedex MongoDB", layout="wide")
st.title("📘 Pokedex con PokeAPI + MongoDB")

tabs = st.tabs([
    "1) Insertar desde PokeAPI",
    "2) Búsqueda + Límite + Ordenación",
    "3) Update",
    "4) Eliminación",
    "5) Borrar colección / DB"
])

# --- TAB 1: INSERT
with tabs[0]:
    st.subheader("Insertar pokemons desde PokeAPI")
    c1, c2 = st.columns(2)
    start_id = c1.number_input("ID inicio", min_value=1, value=1, step=1)
    end_id = c2.number_input("ID fin", min_value=1, value=30, step=1)

    if st.button("📥 Importar / Insertar"):
        with st.spinner("Descargando e insertando..."):
            res = insert_many_from_pokeapi(int(start_id), int(end_id))
        st.success(f"Insertados: {res['inserted']} | Existían: {res['skipped_existing']}")

# --- TAB 2: SEARCH + LIMIT + SORT
with tabs[1]:
    st.subheader("Búsqueda con filtros + paginación (limit/skip) + ordenación")

    col1, col2, col3, col4 = st.columns(4)
    name_contains = col1.text_input("Nombre contiene", value="")
    pokemon_id = col2.number_input("pokemon_id exacto (0 = none)", min_value=0, value=0, step=1)
    type_is = col3.text_input("Tipo exacto (ej: fire, water)", value="")
    limit = col4.slider("Limit", min_value=1, max_value=50, value=10)

    col5, col6, col7, col8 = st.columns(4)
    min_weight = col5.number_input("Peso mínimo (0 none)", min_value=0, value=0, step=1)
    max_weight = col6.number_input("Peso máximo (0 none)", min_value=0, value=0, step=1)
    sort_field = col7.selectbox("Ordenar por", ["pokemon_id", "name", "weight", "height", "base_experience"])
    sort_dir = col8.selectbox("Dirección", ["ASC", "DESC"])

    page = st.number_input("Página (desde 1)", min_value=1, value=1, step=1)
    skip = (int(page) - 1) * int(limit)

    if st.button("🔎 Buscar"):
        res = search_pokemons(
            name_contains=name_contains or None,
            pokemon_id=(int(pokemon_id) if pokemon_id != 0 else None),
            type_is=type_is or None,
            min_weight=(int(min_weight) if min_weight != 0 else None),
            max_weight=(int(max_weight) if max_weight != 0 else None),
            sort_field=sort_field,
            sort_dir=(1 if sort_dir == "ASC" else -1),
            limit=int(limit),
            skip=int(skip),
        )

        st.caption(f"Query usada: {res['query']}")
        st.info(f"Total resultados: {res['total']} | Mostrando: {len(res['results'])} | Página: {page}")

        st.dataframe(res["results"], use_container_width=True)

# --- TAB 3: UPDATE
with tabs[2]:
    st.subheader("Actualizar (update) un pokemon por nombre")
    name = st.text_input("Nombre exacto (ej: pikachu)")
    field = st.selectbox("Campo a actualizar", ["weight", "height", "base_experience", "updated_at"])
    value = st.text_input("Nuevo valor (si es número, escribe número)")

    if st.button("✏️ Actualizar"):
        if not name.strip():
            st.error("Pon un nombre.")
        else:
            # convertir a int si parece número
            try:
                v = int(value)
            except:
                v = value

            res = update_pokemon(name.strip().lower(), {field: v})
            if res.matched_count == 0:
                st.warning("No encontrado.")
            else:
                st.success(f"Actualizado. modified_count={res.modified_count}")

# --- TAB 4: DELETE
with tabs[3]:
    st.subheader("Eliminar documentos")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Eliminar 1 por nombre")
        del_name = st.text_input("Nombre a borrar (ej: bulbasaur)", key="del_name")
        if st.button("🗑️ Borrar por nombre"):
            res = delete_one_by_name(del_name.strip().lower())
            st.info(f"deleted_count={res.deleted_count}")

    with c2:
        st.markdown("### Eliminar muchos por tipo")
        del_type = st.text_input("Tipo a borrar (ej: fire)", key="del_type")
        if st.button("🔥 Borrar por tipo"):
            res = delete_many_by_type(del_type.strip().lower())
            st.info(f"deleted_count={res.deleted_count}")

# --- TAB 5: DROP
with tabs[4]:
    st.subheader("Borrar colección o base de datos completa")

    st.warning("⚠️ Esto elimina datos de forma irreversible.")
    c1, c2 = st.columns(2)

    with c1:
        if st.button("❌ Drop colección (pokemons)"):
            drop_collection()
            st.success("Colección eliminada.")

    with c2:
        if st.button("💣 Drop DATABASE completa"):
            drop_database()
            st.success("Base de datos eliminada.")
