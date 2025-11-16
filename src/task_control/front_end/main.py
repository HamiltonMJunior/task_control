from http import HTTPStatus
from typing import Tuple
import os
import sys

import flet as ft
import requests


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from back_end.settings import Settings  

settings = Settings()
API_BASE_URL = settings.API_BASE_URL

# -------------------------------------------------------------------
# Paleta de cores do layout
# -------------------------------------------------------------------
BG_PAGE = ft.Colors.BLUE_GREY_100
BG_BAR = ft.Colors.BLUE_GREY_700
BORDER_COLOR = ft.Colors.BLUE_GREY_700
TEXT_MUTED = ft.Colors.GREY_700
SYS_BG = ft.Colors.WHITE
SYS_CARD_BG = ft.Colors.BLUE_GREY_50
SYS_TAB_LABEL = ft.Colors.BLUE_GREY_900          
SYS_TAB_LABEL_UNSELECTED = ft.Colors.BLUE_GREY_700
SYS_TAB_INDICATOR = ft.Colors.BLUE_GREY_700      
SYS_TAB_BG = SYS_CARD_BG
SYS_GRID_HEADER_BG = ft.Colors.BLUE_GREY_100
SYS_GRID_HEADER_FG = ft.Colors.BLUE_GREY_900
SYS_GRID_ROW_BG = ft.Colors.WHITE
SYS_GRID_ROW_FG = ft.Colors.BLUE_GREY_900


# -------------------------------------------------------------------
# Helpers genéricos
# -------------------------------------------------------------------
def setup_page(page: ft.Page) -> None:
    page.title = "Controle de Tarefas e Demandas"
    page.theme = ft.Theme(font_family="Poppins")
    page.window_maximized = True
    page.window_full_screen = False
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.bgcolor = BG_PAGE


def show_snack(page: ft.Page, message: str) -> None:
    page.snack_bar = ft.SnackBar(ft.Text(message))
    page.snack_bar.open = True
    page.update()


def primary_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        bgcolor={
            ft.ControlState.DEFAULT: BG_BAR,
            ft.ControlState.HOVERED: ft.Colors.BLUE_GREY_200,
        },
        color={
            ft.ControlState.DEFAULT: ft.Colors.WHITE,
            ft.ControlState.HOVERED: BG_BAR,
        },
    )


# -------------------------------------------------------------------
# Tabs simples em memória (Departamentos, Níveis, Regimes)
# -------------------------------------------------------------------
def build_simple_master_tab(
    page: ft.Page,
    singular_name: str,
    field_label: str,
) -> ft.Column:
    name_field = ft.TextField(label=field_label, width=350)
    items_list = ft.ListView(expand=True, spacing=5, padding=0)

    button_style = primary_button_style()

    def remove_item(
        _: ft.ControlEvent,
        item: ft.Control,
    ) -> None:
        items_list.controls.remove(item)
        page.update()

    def add_item(_: ft.ControlEvent) -> None:
        value = (name_field.value or "").strip()
        if not value:
            return

        tile = ft.ListTile(
            title=ft.Text(value),
            trailing=ft.IconButton(
                ft.Icons.DELETE,
                on_click=lambda e, item_ref=None: remove_item(e, tile),
            ),
        )
        items_list.controls.append(tile)
        name_field.value = ""
        page.update()

    return ft.Column(
        [
            ft.Container(
                padding=ft.padding.only(top=12, bottom=8),
                content=ft.Row(
                    [
                        name_field,
                        ft.ElevatedButton(
                            f"Adicionar {singular_name}",
                            icon=ft.Icons.ADD,
                            on_click=add_item,
                            style=button_style,
                        ),
                    ],
                    spacing=10,
                ),
            ),
            ft.Divider(),
            ft.Text(
                f"{singular_name}s cadastrados:",
                size=14,
                weight=ft.FontWeight.BOLD,
            ),
            items_list,
        ],
        expand=True,
        spacing=10,
    )


# -------------------------------------------------------------------
# Aba de Categorias integrada ao backend
# -------------------------------------------------------------------
def build_category_tab(page: ft.Page) -> ft.Column:
    name_field = ft.TextField(
        label="Nome da Categoria de Relatórios",
        width=350,
        color=TEXT_MUTED,
    )

    # DataTable como "datagrid"
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Descrição")),
            ft.DataColumn(ft.Text("Ações")),
        ],
        rows=[],
        heading_row_color=ft.Colors.BLUE_GREY_100,
        heading_text_style=ft.TextStyle(
            color=ft.Colors.BLUE_GREY_900,
            weight=ft.FontWeight.BOLD,
        ),
        data_text_style=ft.TextStyle(
            color=ft.Colors.BLUE_GREY_900,
        ),
        column_spacing=16,
        divider_thickness=1,
        bgcolor=ft.Colors.WHITE,
        expand=True,  # ocupa o espaço disponível no eixo principal
    )

    button_style = primary_button_style()

    row_even_bg = ft.Colors.BLUE_GREY_50
    row_odd_bg = ft.Colors.WHITE

    def aplicar_zebra() -> None:
        for idx, row in enumerate(table.rows):
            row.color = row_even_bg if idx % 2 == 0 else row_odd_bg

    def abrir_dialog_edicao(cat_id: int, descr_atual: str) -> None:
        txt_edit = ft.TextField(
            label="Descrição da categoria",
            value=descr_atual,
            width=350,
        )

        def salvar_edicao(_: ft.ControlEvent) -> None:
            novo_valor = (txt_edit.value or "").strip()
            if not novo_valor:
                show_snack(page, "Informe a descrição.")
                return

            try:
                resp = requests.put(
                    f"{API_BASE_URL}/category/{cat_id}",
                    json={"descr_tb_category": novo_valor},
                    timeout=5,
                )
                if resp.status_code == HTTPStatus.OK:
                    page.dialog.open = False
                    page.update()
                    load_categories()
                elif resp.status_code == HTTPStatus.CONFLICT:
                    show_snack(
                        page,
                        "Já existe uma categoria com esse nome.",
                    )
                else:
                    show_snack(
                        page,
                        "Erro ao atualizar categoria: "
                        f"{resp.status_code}",
                    )
            except Exception as exc:  # noqa: BLE001
                show_snack(page, f"Erro de conexão ao atualizar: {exc}")

        def fechar_dialog(_: ft.ControlEvent) -> None:
            page.dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar Categoria"),
            content=txt_edit,
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_dialog),
                ft.ElevatedButton("Salvar", on_click=salvar_edicao),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def criar_linha(category: dict) -> ft.DataRow:
        cat_id = category["id_tb_category"]
        descr = category["descr_tb_category"]

        def delete_category(_: ft.ControlEvent) -> None:
            try:
                response = requests.delete(
                    f"{API_BASE_URL}/category/{cat_id}",
                    timeout=5,
                )
            except Exception as exc:  # noqa: BLE001
                show_snack(page, f"Erro de conexão ao excluir: {exc}")
                return

            if response.status_code == HTTPStatus.NO_CONTENT:
                load_categories()
            elif response.status_code == HTTPStatus.NOT_FOUND:
                show_snack(page, "Categoria não encontrada.")
            else:
                show_snack(
                    page,
                    "Erro ao excluir: "
                    f"{response.status_code}",
                )

        def edit_category(_: ft.ControlEvent) -> None:
            abrir_dialog_edicao(cat_id, descr)

        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(str(cat_id))),
                ft.DataCell(ft.Text(descr)),
                ft.DataCell(
                    ft.Row(
                        [
                            ft.IconButton(
                                ft.Icons.EDIT,
                                tooltip="Editar",
                                icon_color=ft.Colors.BLUE_GREY_700,
                                on_click=edit_category,
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE,
                                tooltip="Excluir",
                                icon_color=ft.Colors.RED_400,
                                on_click=delete_category,
                            ),
                        ],
                        spacing=0,
                    )
                ),
            ],
        )

    def load_categories() -> None:
        try:
            response = requests.get(
                f"{API_BASE_URL}/category/",
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()
            table.rows.clear()
            for category in data.get("categories", []):
                table.rows.append(criar_linha(category))
            aplicar_zebra()
            page.update()
        except Exception as exc:  # noqa: BLE001
            show_snack(page, f"Erro ao carregar categorias: {exc}")

    def add_category(_: ft.ControlEvent) -> None:
        valor = (name_field.value or "").strip()
        if not valor:
            show_snack(page, "Informe o nome da categoria.")
            return

        try:
            response = requests.post(
                f"{API_BASE_URL}/category/",
                json={"descr_tb_category": valor},
                timeout=5,
            )
        except Exception as exc:  # noqa: BLE001
            show_snack(page, f"Erro de conexão ao criar: {exc}")
            return

        if response.status_code == HTTPStatus.CREATED:
            name_field.value = ""
            load_categories()
        elif response.status_code == HTTPStatus.CONFLICT:
            show_snack(page, "Categoria já existe.")
        else:
            show_snack(
                page,
                "Erro ao criar categoria: "
                f"{response.status_code}",
            )

    # Carrega dados ao montar a aba
    load_categories()

    header = ft.Container(
        padding=ft.padding.only(top=12, bottom=8),
        content=ft.Row(
            [
                name_field,
                ft.ElevatedButton(
                    "Adicionar Categoria",
                    icon=ft.Icons.ADD,
                    on_click=add_category,
                    style=button_style,
                ),
            ],
            spacing=10,
        ),
    )

    # Container que permite o DataTable ocupar todo o espaço restante
    table_container = ft.Container(
        expand=True,
        content=table,
    )

    return ft.Column(
        [
            header,
            ft.Divider(),
            ft.Text(
                "Categorias cadastradas:",
                size=14,
                weight=ft.FontWeight.BOLD,
                color=TEXT_MUTED,
            ),
            table_container,
        ],
        expand=True,
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


# -------------------------------------------------------------------
# Página Sistema (Tabs)
# -------------------------------------------------------------------
def build_system_page(page: ft.Page) -> ft.Column:
    departments_tab = build_simple_master_tab(
        page,
        singular_name="Departamento",
        field_label="Nome do Departamento",
    )
    levels_tab = build_simple_master_tab(
        page,
        singular_name="Nível",
        field_label="Descrição do Nível de Usuário",
    )
    regimes_tab = build_simple_master_tab(
        page,
        singular_name="Regime",
        field_label="Descrição do Regime Tributário",
    )
    categories_tab = build_category_tab(page)

    tabs = ft.Tabs(
        tabs=[
            ft.Tab(
                text="Departamentos",
                content=ft.Container(
                    padding=ft.padding.only(
                        top=10,
                        left=8,
                        right=8,
                        bottom=8,
                    ),
                    bgcolor=SYS_BG,
                    content=departments_tab,
                ),
            ),
            ft.Tab(
                text="Níveis de Usuário",
                content=ft.Container(
                    padding=ft.padding.only(
                        top=10,
                        left=8,
                        right=8,
                        bottom=8,
                    ),
                    bgcolor=SYS_BG,
                    content=levels_tab,
                ),
            ),
            ft.Tab(
                text="Regimes Tributários",
                content=ft.Container(
                    padding=ft.padding.only(
                        top=10,
                        left=8,
                        right=8,
                        bottom=8,
                    ),
                    bgcolor=SYS_BG,
                    content=regimes_tab,
                ),
            ),
            ft.Tab(
                text="Categorias",
                content=ft.Container(
                    padding=ft.padding.only(
                        top=10,
                        left=8,
                        right=8,
                        bottom=8,
                    ),
                    bgcolor=SYS_BG,
                    content=categories_tab,
                ),
            ),
        ],
        expand=1,
        label_color=SYS_TAB_LABEL,
        unselected_label_color=SYS_TAB_LABEL_UNSELECTED,
        indicator_color=SYS_TAB_INDICATOR,
    )

    description = (
        "Cadastre aqui departamentos, níveis de usuário, "
        "regimes tributários e categorias de relatórios."
    )

    return ft.Column(
        [
            ft.Text(
                "Configurações do Sistema",
                size=22,
                weight=ft.FontWeight.BOLD,
                color=TEXT_MUTED,
            ),
            ft.Text(
                description,
                size=14,
                color=TEXT_MUTED,
            ),
            ft.Divider(),
            tabs,
        ],
        expand=True,
        spacing=10,
    )


# -------------------------------------------------------------------
# Funções que trocam o conteúdo central
# -------------------------------------------------------------------
def show_dashboard(page: ft.Page, content_column: ft.Column) -> None:
    content_column.controls = [
        ft.Text(
            "Início",
            size=24,
            weight=ft.FontWeight.BOLD,
        ),
        ft.Text(
            "Bem-vindo ao Controle de Tarefas e Demandas",
            size=16,
        ),
    ]
    page.update()


def show_system(page: ft.Page, content_column: ft.Column) -> None:
    content_column.controls = [build_system_page(page)]
    page.update()


def show_placeholder(
    page: ft.Page,
    content_column: ft.Column,
    title: str,
) -> None:
    content_column.controls = [
        ft.Text(title, size=22, weight=ft.FontWeight.BOLD),
        ft.Text(
            "Tela ainda não implementada. "
            "Aqui vai o formulário específico.",
            size=14,
            color=TEXT_MUTED,
        ),
    ]
    page.update()


# -------------------------------------------------------------------
# Layout: top bar, sidebar, container de conteúdo
# -------------------------------------------------------------------
def toggle_sidebar(
    _: ft.ControlEvent,
    side_bar: ft.Container,
    page: ft.Page,
) -> None:
    side_bar.width = 0 if side_bar.width > 0 else 220
    page.update()


def create_top_bar(on_menu_click) -> ft.Container:
    return ft.Container(
        bgcolor=BG_BAR,
        height=60,
        padding=ft.padding.symmetric(horizontal=16),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=6,
            color=ft.Colors.BLACK45,
            offset=ft.Offset(0, 2),
        ),
        content=ft.Row(
            [
                ft.Row(
                    [
                        ft.IconButton(
                            ft.Icons.MENU,
                            on_click=on_menu_click,
                        ),
                        ft.Text(
                            value="Controle de Tarefas e Demandas",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    spacing=10,
                ),
                ft.Row(
                    [
                        ft.IconButton(ft.Icons.SEARCH),
                        ft.IconButton(ft.Icons.NOTIFICATIONS),
                        ft.CircleAvatar(
                            content=ft.Text(value="HM"),
                        ),
                    ],
                    spacing=5,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def create_side_bar(
    page: ft.Page,
    content_column: ft.Column,
) -> ft.Container:
    return ft.Container(
        bgcolor=BG_BAR,
        width=220,
        animate=ft.Animation(200, "ease-in-out"),
        content=ft.Column(
            [
                ft.Text(
                    "Menu",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                ft.TextButton(
                    "Início",
                    icon=ft.Icons.HOME,
                    on_click=lambda e: show_dashboard(
                        page,
                        content_column,
                    ),
                ),
                ft.TextButton(
                    "Sistema",
                    icon=ft.Icons.SETTINGS,
                    on_click=lambda e: show_system(
                        page,
                        content_column,
                    ),
                ),
                ft.TextButton(
                    "Usuários",
                    icon=ft.Icons.PERSON,
                    on_click=lambda e: show_placeholder(
                        page,
                        content_column,
                        "Usuários",
                    ),
                ),
                ft.TextButton(
                    "Clientes",
                    icon=ft.Icons.ACCOUNT_BOX_SHARP,
                    on_click=lambda e: show_placeholder(
                        page,
                        content_column,
                        "Clientes",
                    ),
                ),
                ft.TextButton(
                    "Demandas Clientes",
                    icon=ft.Icons.TAB_SHARP,
                    on_click=lambda e: show_placeholder(
                        page,
                        content_column,
                        "Demandas Clientes",
                    ),
                ),
                ft.TextButton(
                    "Tarefas-Rotinas",
                    icon=ft.Icons.TAB_ROUNDED,
                    on_click=lambda e: show_placeholder(
                        page,
                        content_column,
                        "Tarefas-Rotinas",
                    ),
                ),
                ft.Container(expand=True),
                ft.TextButton(
                    "Sair",
                    icon=ft.Icons.EXIT_TO_APP,
                    on_click=lambda e: page.window.close(),
                ),
            ],
            expand=True,
        ),
    )


def create_content_components() -> Tuple[ft.Column, ft.Container]:
    content_column = ft.Column(expand=True, spacing=10)
    content_container = ft.Container(
        expand=True,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=10,
        padding=10,
        content=content_column,
    )
    return content_column, content_container


def build_root_layout(
    top_bar: ft.Container,
    side_bar: ft.Container,
    content_container: ft.Container,
) -> ft.Column:
    return ft.Column(
        [
            top_bar,
            ft.Row(
                [
                    side_bar,
                    content_container,
                ],
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        ],
        expand=True,
    )


def main(page: ft.Page) -> None:
    setup_page(page)

    content_column, content_container = create_content_components()
    side_bar = create_side_bar(page, content_column)

    top_bar = create_top_bar(
        lambda e: toggle_sidebar(e, side_bar, page),
    )

    root_layout = build_root_layout(
        top_bar,
        side_bar,
        content_container,
    )
    page.add(root_layout)

    show_dashboard(page, content_column)


ft.app(target=main)
