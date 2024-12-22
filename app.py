import dash
from dash import dcc, html, Input, Output, State, ALL
import plotly.graph_objs as go
from datetime import datetime
import json
from request_funcs import get_localoties, get_multiday_forecast


app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Прогноз погоды"

api_key = input("Введить API-ключ: ")


# ---------------------------
# Основное хранилище и корневой layout
# ---------------------------
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="store_candidates", data={}),
    dcc.Store(id="store_chosen", data=[]),
    dcc.Store(id="store_days", data=5),
    dcc.Store(id="store_raw_points", data=[]),
    html.Div(id="page-content")
])


# ---------------------------
# Страница 1: Ввод локаций
# ---------------------------
page_input_layout = html.Div([
    html.H1("Введите локации и число дней"),
    html.Label("Введите названия локаций (до 5):"),
    html.Div([
        dcc.Input(id="loc1", type="text", placeholder="Локация 1"),
        html.Br(),
        dcc.Input(id="loc2", type="text", placeholder="Локация 2"),
        html.Br(),
        dcc.Input(id="loc3", type="text", placeholder="Локация 3"),
        html.Br(),
        dcc.Input(id="loc4", type="text", placeholder="Локация 4"),
        html.Br(),
        dcc.Input(id="loc5", type="text", placeholder="Локация 5"),
    ]),
    html.Br(),
    html.Label("Количество дней прогноза:"),
    dcc.Dropdown(
        id="days-dropdown",
        options=[
            {"label": "1 день", "value": 1},
            {"label": "3 дня", "value": 3},
            {"label": "5 дней", "value": 5}
        ],
        value=5,
        clearable=False,
        style={"width": "200px"}
    ),
    html.Br(),
    html.Button("Далее", id="button-go-choice"),
    html.Div(id="page1-error", style={"color": "red", "marginTop": "20px"})
])


# ---------------------------
# Страница 2: Выбор локаций
# ---------------------------
def make_choice_layout(candidates):
    if not candidates:
        return html.Div([
            html.H1("Выбор локации"),
            html.Div("Нет кандидатов для выбора или произошла ошибка.", style={"color": "red"})
        ])

    blocks = []
    for idx, loc_list in candidates.items():
        if not loc_list:
            blocks.append(html.Div([
                html.H3(f"Локация #{int(idx)+1}: не найдены варианты", style={"color": "red"})
            ]))
        else:
            rows = []
            for j, (country, region, city, key_) in enumerate(loc_list):
                val_dict = {"loc_index": idx, "cand_index": j}
                radio = dcc.RadioItems(
                    id={"type": "radio", "group_index": idx, "cand_index": j},
                    options=[{"label": "", "value": json.dumps(val_dict)}],
                    value=None
                )
                rows.append(html.Tr([
                    html.Td(j+1),
                    html.Td(country),
                    html.Td(region),
                    html.Td(city),
                    html.Td(radio)
                ]))

            table = html.Table([
                html.Thead(html.Tr([
                    html.Th("№"), html.Th("Страна"), html.Th("Регион"),
                    html.Th("Город"), html.Th("Выбор")
                ])),
                html.Tbody(rows)
            ], style={"border": "1px solid black", "borderCollapse": "collapse"})

            blocks.append(html.Div([
                html.H3(f"Локация #{int(idx)+1}, найдено {len(loc_list)} вариантов:"),
                table
            ]))
        blocks.append(html.Hr())

    return html.Div([
        html.H1("Выбор локаций"),
        html.Div(blocks),
        html.Button("Показать прогноз", id="button-go-weather"),
        html.Div(id="page2-error", style={"color": "red", "marginTop": "20px"})
    ])


# ---------------------------
# Страница 3: Показ прогнозов
# ---------------------------
def make_weather_layout(chosen_data, days):
    if not chosen_data:
        return html.Div([
            html.H1("Результат"),
            html.Div("Не выбрано ни одной локации.", style={"color": "red"})
        ])

    blocks = []
    for city_name, loc_key in chosen_data:
        forecast = get_multiday_forecast(api_key, loc_key, days)
        if not forecast:
            blocks.append(html.Div([
                html.H2(city_name),
                html.Div("Ошибка получения прогноза", style={"color": "red"})
            ]))
            continue

        dates, temps, rains, winds = [], [], [], []
        for item in forecast:
            date_str = item["Date"]
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', ''))
                dates.append(date_obj.date().isoformat())
            except ValueError:
                dates.append(date_str)
            temps.append(item["MeanTempC"])
            rains.append(item["RainProb"])
            winds.append(item["WindSpeedKmH"])

        fig_temp = go.Figure(data=[go.Scatter(x=dates, y=temps, mode='lines+markers')])
        fig_temp.update_layout(title=f"Температура — {city_name}", xaxis_title="Дата", yaxis_title="°C")

        fig_rain = go.Figure(data=[go.Bar(x=dates, y=rains)])
        fig_rain.update_layout(title=f"Вероятность дождя — {city_name}", xaxis_title="Дата", yaxis_title="%")

        fig_wind = go.Figure(data=[go.Scatter(x=dates, y=winds, mode='lines+markers')])
        fig_wind.update_layout(title=f"Скорость ветра — {city_name}", xaxis_title="Дата", yaxis_title="км/ч")

        blocks.append(html.Div([
            html.H2(city_name),
            dcc.Graph(figure=fig_temp),
            dcc.Graph(figure=fig_rain),
            dcc.Graph(figure=fig_wind),
            html.Hr()
        ]))

    return html.Div([
        html.H1("Прогноз погоды"),
        html.Div(blocks)
    ])


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    State("store_candidates", "data"),
    State("store_chosen", "data"),
    State("store_days", "data")
)
def display_page(pathname, candidates, chosen, days):
    if pathname in [None, "/"]:
        return page_input_layout
    if pathname == "/location_choice":
        return make_choice_layout(candidates)
    if pathname == "/weather":
        return make_weather_layout(chosen, days)
    return html.Div("Страница не найдена", style={"color": "red"})


@app.callback(
    Output("url", "pathname"),
    Output("page1-error", "children"),
    Output("store_candidates", "data"),
    Output("store_days", "data"),
    Output("store_raw_points", "data"),
    Input("button-go-choice", "n_clicks"),
    State("loc1", "value"),
    State("loc2", "value"),
    State("loc3", "value"),
    State("loc4", "value"),
    State("loc5", "value"),
    State("days-dropdown", "value"),
    prevent_initial_call=True
)
def handle_step1(n_clicks, loc1, loc2, loc3, loc4, loc5, days):
    # Всего 5 выходных параметров → нужно возвращать ровно 5 значений.
    if not n_clicks:
        return (dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update)

    raw_points = [p.strip() for p in [loc1, loc2, loc3, loc4, loc5] if p and p.strip()]
    if not raw_points:
        # Возвращаем 5 значений (url, сообщение, store_candidates, store_days, store_raw_points)
        return None, "Введите хотя бы одну локацию", {}, 5, []

    candidates = {}
    for idx, city_name in enumerate(raw_points):
        locs = get_localoties(api_key, city_name)
        candidates[idx] = locs if locs else []

    # Также 5 значений
    return "/location_choice", "", candidates, days, raw_points


@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("page2-error", "children"),
    Output("store_chosen", "data"),
    Input("button-go-weather", "n_clicks"),
    State("store_candidates", "data"),
    State({"type": "radio", "group_index": ALL, "cand_index": ALL}, "value"),
    prevent_initial_call=True
)
def handle_step2(n_clicks, candidates, radio_values):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    if not candidates:
        return None, "Нет вариантов для выбора.", []

    chosen_map = {}
    for val in radio_values:
        if val:
            info = json.loads(val)
            chosen_map[info["loc_index"]] = info["cand_index"]

    if not chosen_map:
        return None, "Не выбрана ни одна локация.", []

    chosen_list = []
    for idx in sorted(chosen_map):
        cand_list = candidates.get(str(idx), [])
        cand_idx = chosen_map[idx]
        if cand_idx < len(cand_list):
            _, _, city, key_ = cand_list[cand_idx]
            chosen_list.append((city, key_))

    return "/weather", "", chosen_list


if __name__ == "__main__":
    app.run_server(debug=True)
