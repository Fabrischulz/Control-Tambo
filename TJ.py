# Importación de módulos necesarios
import sys  # Proporciona acceso a funciones y objetos del intérprete de Python.
from datetime import datetime, timedelta  # Manejo de fechas y tiempos.
import sqlite3  # Para interactuar con bases de datos SQLite.
import tkinter as tk  # Para crear interfaces gráficas simples.
from PyQt6.QtWidgets import (  # Componentes de PyQt6 para interfaces gráficas avanzadas.
    QApplication, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QLineEdit, QHBoxLayout, QMessageBox, QInputDialog, QHeaderView
)
from PyQt6.QtGui import QColor  # Para manejar colores en la interfaz.
from PyQt6.QtCore import Qt, QTimer  # Para manejar alineaciones y temporizadores.
import requests

__version__ = "1.1.3"

# Función para inicializar la base de datos SQLite
def initialize_db():
    """Inicializa la base de datos SQLite y asegura que todas las columnas necesarias existan"""
    conn = sqlite3.connect("clientes.db")
    cursor = conn.cursor()

    # Verificar si faltan columnas en la tabla
    cursor.execute("PRAGMA table_info(clientes)")
    columns = [column[1] for column in cursor.fetchall()]

    if "ultimo_cambio_pezoneras" not in columns:
        cursor.execute("ALTER TABLE clientes ADD COLUMN ultimo_cambio_pezoneras TEXT")
    if "proximo_cambio_pezoneras" not in columns:
        cursor.execute("ALTER TABLE clientes ADD COLUMN proximo_cambio_pezoneras TEXT")
    if "proximo_cambio_mangueras" not in columns:
        cursor.execute("ALTER TABLE clientes ADD COLUMN proximo_cambio_mangueras TEXT")
    if "ordenes" not in columns:
        cursor.execute("ALTER TABLE clientes ADD COLUMN ordenes INTEGER DEFAULT 0")
    if "bajadas" not in columns:
        cursor.execute("ALTER TABLE clientes ADD COLUMN bajadas INTEGER DEFAULT 0")
    if "ultimo_chequeo" not in columns:
        cursor.execute("ALTER TABLE clientes ADD COLUMN ultimo_chequeo TEXT")
    if "proximo_chequeo" not in columns:
        cursor.execute("ALTER TABLE clientes ADD COLUMN proximo_chequeo TEXT")
    if "ultimo_cambio_pulsadores" not in columns:
        cursor.execute("ALTER TABLE clientes ADD COLUMN ultimo_cambio_pulsadores TEXT")
    if "proximo_cambio_pulsadores" not in columns:
        cursor.execute("ALTER TABLE clientes ADD COLUMN proximo_cambio_pulsadores TEXT")

    conn.commit()
    conn.close()

# Clase principal de la aplicación PyQt6
class ClienteApp(QWidget):
    def __init__(self):
        """Inicializa la ventana principal de la aplicación"""
        super().__init__()
        self.setWindowTitle("Gestión de Pezoneras")  # Título de la ventana.
        self.showMaximized()  # Abre la ventana en pantalla completa.
        self.setStyle()  # Aplica estilos personalizados.
        self.initUI()  # Inicializa la interfaz gráfica.
        self.load_data()  # Carga los datos de la base de datos en la tabla.

    def setStyle(self):
        """Define el estilo visual de los botones en la aplicación"""
        self.setStyleSheet("""
            QPushButton {
                background-color: #8B4513; /* Color marrón */
                color: white; /* Texto blanco */
                border-radius: 5px; /* Bordes redondeados */
                padding: 8px; /* Espaciado interno */
            }
            QPushButton:hover {
                background-color: #A0522D; /* Color marrón más claro al pasar el mouse */
            }
            QPushButton:pressed {
                background-color: #5C2E0F; /* Color marrón oscuro al presionar */
            }
        """)

    def initUI(self):
        """Inicializa la interfaz gráfica de usuario de la aplicación"""
        layout = QVBoxLayout()  # Diseño vertical para los widgets.

        # Contenedor para la fecha y el botón de salir
        header_layout = QHBoxLayout()

        # Etiqueta para mostrar la fecha actual en la esquina superior derecha.
        self.date_label = QLabel(datetime.now().strftime("%Y-%m-%d"), self)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(self.date_label)

        # Botón para salir del sistema
        self.exit_button = QPushButton("Salir")
        self.exit_button.setFixedSize(100, 40)  # Tamaño fijo: ancho 100px, alto 40px
        self.exit_button.clicked.connect(self.exit_system)  # Conecta el botón al método `exit_system`.
        header_layout.addWidget(self.exit_button)

        layout.addLayout(header_layout)

        # Tabla para mostrar los datos de los clientes.
        self.table = QTableWidget()
        self.table.setColumnCount(16)  # Cambiar de 13 a 16 columnas
        self.table.setHorizontalHeaderLabels([
            "Cliente", "Vacas", "Ordeñes", "Bajadas", "Último Cambio de Pezoneras",  
            "Próximo Cambio", "Cambio de Pezoneras", "Último Cambio de Mangueras", 
            "Próximo Cambio de Mangueras", "Marcar Cambio de Mangueras",
            "Último Cambio de Pulsador", "Próximo Cambio de Pulsador", "Marcar Cambio de Pulsador",
            "Fecha de Último Chequeo", "Fecha del Próximo Chequeo", "Marcar Chequeo"
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Deshabilita la edición directa.
        layout.addWidget(self.table)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)  # Ajusta el tamaño de las columnas al contenido.

        # Formulario para añadir un cliente.
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del Cliente")
        self.vacas_input = QLineEdit()
        self.vacas_input.setPlaceholderText("Cantidad de Vacas")
        self.fecha_input = QLineEdit()  # Campo para la fecha del cambio.
        self.fecha_input.setPlaceholderText("Fecha de Cambio (YYYY-MM-DD)")
        self.add_button = QPushButton("Añadir Cliente")
        self.add_button.clicked.connect(self.add_cliente)  # Conecta el botón a la función `add_cliente`.
        self.ordenes_input = QLineEdit()
        self.ordenes_input.setPlaceholderText("Ordeñes")
        self.bajadas_input = QLineEdit()
        self.bajadas_input.setPlaceholderText("Bajadas")
        self.cambio_mangueras_input = QLineEdit()
        self.cambio_mangueras_input.setPlaceholderText("Último Cambio de Mangueras (YYYY-MM-DD)")
        self.cambio_pulsadores_input = QLineEdit()
        self.cambio_pulsadores_input.setPlaceholderText("Última Fecha de Cambio de Pulsadores (YYYY-MM-DD)")
        self.ultimo_chequeo_input = QLineEdit()
        self.ultimo_chequeo_input.setPlaceholderText("Último Chequeo (YYYY-MM-DD)")

        # Añade los campos al formulario.
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.vacas_input)
        form_layout.addWidget(self.fecha_input)
        form_layout.addWidget(self.add_button)
        layout.addLayout(form_layout)
        form_layout.addWidget(self.ordenes_input)
        form_layout.addWidget(self.bajadas_input)
        form_layout.addWidget(self.cambio_mangueras_input)
        form_layout.addWidget(self.cambio_pulsadores_input)
        form_layout.addWidget(self.ultimo_chequeo_input)

        # Botón para modificar la cantidad de vacas de un cliente.
        self.modify_button = QPushButton("Modificar Cantidad de Vacas")
        self.modify_button.clicked.connect(self.select_cliente_para_modificar)
        layout.addWidget(self.modify_button)

        # Botón para modificar la cantidad de ordeñes de un cliente.
        self.modify_ordenes_button = QPushButton("Modificar cantidad de ordeñes")
        self.modify_ordenes_button.clicked.connect(self.select_cliente_para_modificar_ordenes)
        layout.addWidget(self.modify_ordenes_button)

        # Botón para modificar la cantidad de bajadas de un cliente.
        self.modify_bajadas_button = QPushButton("Modificar cantidad de bajadas")
        self.modify_bajadas_button.clicked.connect(self.select_cliente_para_modificar_bajadas)
        layout.addWidget(self.modify_bajadas_button)

        # Botón para eliminar un cliente.
        self.delete_button = QPushButton("Eliminar Cliente")
        self.delete_button.clicked.connect(self.delete_cliente)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)  # Establece el diseño principal.

        # Temporizador para actualizar la fecha cada minuto.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_date)
        self.timer.start(60000)  # Actualiza cada 1 minuto.

    def update_date(self):
        """Actualiza la fecha mostrada en la etiqueta"""
        self.date_label.setText(datetime.now().strftime("%Y-%m-%d"))

    def add_cliente(self):
        """Añade un nuevo cliente a la base de datos con validaciones más estrictas"""
        # Validaciones de los campos de entrada.
        nombre = self.name_input.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return

        try:
            vacas = int(self.vacas_input.text().strip())
            if vacas <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "La cantidad de vacas debe ser un número positivo.")
            return

        fecha_cambio = self.fecha_input.text().strip()
        try:
            datetime.strptime(fecha_cambio, "%Y-%m-%d")
        except ValueError:
            QMessageBox.warning(self, "Error", "La fecha debe estar en formato YYYY-MM-DD.")
            return

        try:
            ordenes = int(self.ordenes_input.text().strip())
            bajadas = int(self.bajadas_input.text().strip())
            if ordenes <= 0 or bajadas <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Ordeñes y Bajadas deben ser números positivos.")
            return

        # Validar la Última Fecha de Chequeo
        ultimo_chequeo = self.ultimo_chequeo_input.text().strip()
        if ultimo_chequeo:
            try:
                datetime.strptime(ultimo_chequeo, "%Y-%m-%d")
            except ValueError:
                QMessageBox.warning(self, "Error", "La fecha de último chequeo debe estar en formato YYYY-MM-DD.")
                return
        else:
            ultimo_chequeo = "Sin datos"  # Valor por defecto si no se ingresa nada

        # Validar la Última Fecha de Cambio de Pulsadores
        ultima_fecha_cambio_pulsadores = self.cambio_pulsadores_input.text().strip()
        if ultima_fecha_cambio_pulsadores:
            try:
                datetime.strptime(ultima_fecha_cambio_pulsadores, "%Y-%m-%d")
            except ValueError:
                QMessageBox.warning(self, "Error", "La fecha de cambio de pulsadores debe estar en formato YYYY-MM-DD.")
                return
        else:
            ultima_fecha_cambio_pulsadores = "Sin datos"  # Valor por defecto si no se ingresa nada

        # Validar la Última Fecha de Cambio de Mangueras
        ultima_fecha_cambio_mangueras = self.cambio_mangueras_input.text().strip()
        if ultima_fecha_cambio_mangueras:
            try:
                datetime.strptime(ultima_fecha_cambio_mangueras, "%Y-%m-%d")
            except ValueError:
                QMessageBox.warning(self, "Error", "La fecha de cambio de mangueras debe estar en formato YYYY-MM-DD.")
                return
        else:
            ultima_fecha_cambio_mangueras = "Sin datos"  # Valor por defecto si no se ingresa nada

        # Validar la Última Fecha de Cambio de Pezoneras
        ultima_fecha_cambio_pezoneras = self.fecha_input.text().strip()
        if ultima_fecha_cambio_pezoneras:
            try:
                datetime.strptime(ultima_fecha_cambio_pezoneras, "%Y-%m-%d")
            except ValueError:
                QMessageBox.warning(self, "Error", "La fecha de cambio de pezoneras debe estar en formato YYYY-MM-DD.")
                return
        else:
            ultima_fecha_cambio_pezoneras = "Sin datos"  # Valor por defecto si no se ingresa nada

        # Calcular el Próximo Cambio de Pezoneras (Columna 5)
        if ultima_fecha_cambio_pezoneras != "Sin datos" and vacas > 0 and ordenes > 0 and bajadas > 0:
            dias_adicionales = 2500 / (vacas * (ordenes / bajadas))
            dias_adicionales = int(dias_adicionales)
            fecha_ultimo_cambio = datetime.strptime(ultima_fecha_cambio_pezoneras, "%Y-%m-%d")
            proximo_cambio_pezoneras = (fecha_ultimo_cambio + timedelta(days=dias_adicionales)).strftime("%Y-%m-%d")
        else:
            proximo_cambio_pezoneras = "Sin datos"

        # Calcular el Próximo Chequeo (Columna 14)
        if ultimo_chequeo != "Sin datos" and vacas > 0 and ordenes > 0 and bajadas > 0:
            dias_adicionales_chequeo = 7000 / (vacas * (ordenes / bajadas))
            dias_adicionales_chequeo = int(dias_adicionales_chequeo)
            fecha_ultimo_chequeo = datetime.strptime(ultimo_chequeo, "%Y-%m-%d")
            proximo_chequeo = (fecha_ultimo_chequeo + timedelta(days=dias_adicionales_chequeo)).strftime("%Y-%m-%d")
        else:
            proximo_chequeo = "Sin datos"

        # Fecha inicial para la columna 7
        proximo_cambio_mangueras = datetime.now().strftime("%Y-%m-%d")

        # Inserta los datos en la base de datos
        conn = sqlite3.connect("clientes.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clientes (nombre, vacas, ultimo_cambio, intervalo, ultimo_cambio_pezoneras, 
                                  proximo_cambio_mangueras, ordenes, bajadas, ultimo_cambio_pulsadores, 
                                  proximo_cambio_pezoneras, ultimo_chequeo, proximo_chequeo) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, vacas, fecha_cambio, 0, ultima_fecha_cambio_pezoneras, ultima_fecha_cambio_mangueras, 
              ordenes, bajadas, ultima_fecha_cambio_pulsadores, proximo_cambio_pezoneras, ultimo_chequeo, proximo_chequeo))
        conn.commit()
        conn.close()

        self.load_data()  # Recarga los datos en la tabla.
        QMessageBox.information(self, "Éxito", "Cliente agregado correctamente.")
        self.clear_inputs()  # Limpia los campos de entrada.

    def clear_inputs(self):
        """Limpia los campos de entrada después de agregar un cliente"""
        self.name_input.clear()
        self.vacas_input.clear()
        self.fecha_input.clear()
        self.ordenes_input.clear()
        self.bajadas_input.clear()
        self.cambio_mangueras_input.clear()
        self.cambio_pulsadores_input.clear()
        self.ultimo_chequeo_input.clear()
        self.ultimo_chequeo_input.clear()

    def load_data(self):
        """Carga y muestra los datos de los clientes en la tabla"""
        self.table.setRowCount(0)  # Limpia la tabla.
        conn = sqlite3.connect("clientes.db")
        cursor = conn.cursor()
        # Ordenar los clientes alfabéticamente por nombre
        cursor.execute("""
            SELECT id, nombre, vacas, ultimo_cambio, intervalo, ultimo_cambio_pezoneras, 
                   proximo_cambio_pezoneras, proximo_cambio_mangueras, ordenes, bajadas, 
                   ultimo_cambio_pulsadores, proximo_cambio_pulsadores, 
                   ultimo_chequeo, proximo_chequeo
            FROM clientes 
            ORDER BY nombre ASC
        """)
        clientes = cursor.fetchall()
        conn.close()

        for row_idx, cliente in enumerate(clientes):
            # Desglosa los valores de cliente
            (id_cliente, nombre, vacas, ultimo_cambio, intervalo, ultimo_cambio_pezoneras, 
             proximo_cambio_pezoneras, proximo_cambio_mangueras, ordenes, bajadas, 
             ultimo_cambio_pulsadores, proximo_cambio_pulsadores, 
             ultimo_chequeo, proximo_chequeo) = cliente

            # Insertar datos en la tabla
            self.table.insertRow(row_idx)

            # Columna 0: Nombre del Cliente (asociar el ID del cliente)
            nombre_item = QTableWidgetItem(nombre)
            nombre_item.setData(Qt.ItemDataRole.UserRole, id_cliente)  # Asociar el ID del cliente
            self.table.setItem(row_idx, 0, nombre_item)

            # Columna 1: Vacas
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(vacas)))

            # Columna 2: Ordeñes
            ordenes_item = QTableWidgetItem(str(ordenes))
            ordenes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 2, ordenes_item)

            # Columna 3: Bajadas
            bajadas_item = QTableWidgetItem(str(bajadas))
            bajadas_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 3, bajadas_item)

            # Columna 4: Último Cambio de Pezoneras
            if ultimo_cambio_pezoneras is None or ultimo_cambio_pezoneras == "Sin datos":
                ultimo_cambio_pezoneras = "Sin datos"
            ultimo_cambio_item = QTableWidgetItem(ultimo_cambio_pezoneras)
            ultimo_cambio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 4, ultimo_cambio_item)

            # Columna 5: Próximo Cambio de Pezoneras
            if proximo_cambio_pezoneras is None or proximo_cambio_pezoneras == "Sin datos":
                proximo_cambio_pezoneras = "Sin datos"
            proximo_cambio_item = QTableWidgetItem(proximo_cambio_pezoneras)
            proximo_cambio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if proximo_cambio_pezoneras != "Sin datos":
                dias_restantes = (datetime.strptime(proximo_cambio_pezoneras, "%Y-%m-%d") - datetime.now()).days
                self.colorear_celda(proximo_cambio_item, dias_restantes)
            self.table.setItem(row_idx, 5, proximo_cambio_item)

            # Columna 6: Botón para marcar cambio de pezoneras
            btn_pezoneras = QPushButton("Marcar Cambio")
            btn_pezoneras.clicked.connect(self.create_marcar_cambio_pezoneras_handler(id_cliente, row_idx))
            self.table.setCellWidget(row_idx, 6, btn_pezoneras)

            # Columna 7: Último Cambio de Mangueras
            if ultimo_cambio is None or ultimo_cambio == "Sin datos":
                ultimo_cambio = "Sin datos"
            ultimo_cambio_item = QTableWidgetItem(ultimo_cambio)
            ultimo_cambio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 7, ultimo_cambio_item)

            # Columna 8: Próximo Cambio de Mangueras
            if proximo_cambio_mangueras is None or proximo_cambio_mangueras == "Sin datos":
                proximo_cambio_mangueras = "Sin datos"
            proximo_cambio_item = QTableWidgetItem(proximo_cambio_mangueras)
            proximo_cambio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if proximo_cambio_mangueras != "Sin datos":
                dias_restantes = (datetime.strptime(proximo_cambio_mangueras, "%Y-%m-%d") - datetime.now()).days
                self.colorear_celda(proximo_cambio_item, dias_restantes)
            self.table.setItem(row_idx, 8, proximo_cambio_item)

            # Columna 9: Botón para marcar cambio de mangueras
            btn_mangueras = QPushButton("Marcar Cambio de Manguera")
            btn_mangueras.clicked.connect(self.create_marcar_cambio_mangueras_handler(id_cliente, row_idx))
            self.table.setCellWidget(row_idx, 9, btn_mangueras)

            # Columna 10: Último Cambio de Pulsador
            if ultimo_cambio_pulsadores is None:
                ultimo_cambio_pulsadores = "Sin datos"
            ultimo_cambio_pulsadores_item = QTableWidgetItem(ultimo_cambio_pulsadores)
            ultimo_cambio_pulsadores_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 10, ultimo_cambio_pulsadores_item)

            # Columna 11: Próximo Cambio de Pulsador
            if ultimo_cambio_pulsadores is None or ultimo_cambio_pulsadores == "Sin datos":
                proximo_cambio_pulsadores_item = QTableWidgetItem("Sin datos")
            else:
                try:
                    vacas_item = self.table.item(row_idx, 1)
                    vacas = int(vacas_item.text()) if vacas_item else 0

                    ordenes_item = self.table.item(row_idx, 2)
                    ordenes = int(ordenes_item.text()) if ordenes_item else 0

                    bajadas_item = self.table.item(row_idx, 3)
                    bajadas = int(bajadas_item.text()) if bajadas_item else 0

                    if vacas > 0 and ordenes > 0 and bajadas > 0:
                        dias_adicionales = 7000 / (vacas * (ordenes / bajadas))
                        dias_adicionales = int(dias_adicionales)

                        # Calcular la fecha del próximo cambio usando la fecha de la columna 10
                        fecha_ultimo_cambio = datetime.strptime(ultimo_cambio_pulsadores, "%Y-%m-%d")
                        proximo_cambio = fecha_ultimo_cambio + timedelta(days=dias_adicionales)
                        proximo_cambio_pulsadores_item = QTableWidgetItem(proximo_cambio.strftime("%Y-%m-%d"))

                        # Aplicar color según los días restantes
                        dias_restantes = (proximo_cambio - datetime.now()).days
                        self.colorear_celda(proximo_cambio_pulsadores_item, dias_restantes)
                    else:
                        proximo_cambio_pulsadores_item = QTableWidgetItem("Sin datos")
                except Exception:
                    proximo_cambio_pulsadores_item = QTableWidgetItem("Error")

            self.table.setItem(row_idx, 11, proximo_cambio_pulsadores_item)

            # Columna 12: Botón para marcar cambio de pulsadores
            btn_pulsadores = QPushButton("Marcar Cambio de Pulsador")
            btn_pulsadores.clicked.connect(self.create_marcar_cambio_pulsadores_handler(id_cliente, row_idx))
            self.table.setCellWidget(row_idx, 12, btn_pulsadores)

            # Columna 13: Fecha de Último Chequeo
            if ultimo_chequeo is None or ultimo_chequeo == "Sin datos":
                ultimo_chequeo = "Sin datos"
            ultimo_chequeo_item = QTableWidgetItem(ultimo_chequeo)
            ultimo_chequeo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 13, ultimo_chequeo_item)

            # Columna 14: Fecha del Próximo Chequeo
            if proximo_chequeo is None or proximo_chequeo == "Sin datos":
                proximo_chequeo = "Sin datos"
            proximo_chequeo_item = QTableWidgetItem(proximo_chequeo)
            proximo_chequeo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if proximo_chequeo != "Sin datos":
                dias_restantes = (datetime.strptime(proximo_chequeo, "%Y-%m-%d") - datetime.now()).days
                self.colorear_celda(proximo_chequeo_item, dias_restantes)
            self.table.setItem(row_idx, 14, proximo_chequeo_item)

            # Columna 15: Botón para marcar chequeo
            btn_chequeo = QPushButton("Marcar Chequeo")
            btn_chequeo.clicked.connect(self.create_marcar_chequeo_handler(id_cliente, row_idx))
            self.table.setCellWidget(row_idx, 15, btn_chequeo)

        # Forzar el ordenamiento alfabético en la tabla
        self.table.sortItems(0, Qt.SortOrder.AscendingOrder)

    def marcar_cambio_pezoneras(self, id_cliente, row_idx):
        """Marca un cambio de pezoneras para un cliente, actualiza la columna 4 y recalcula la columna 5"""
        try:
            nueva_fecha = datetime.now().strftime("%Y-%m-%d")  # Fecha actual

            # Actualizar la fecha de último cambio de pezoneras en la base de datos
            conn = sqlite3.connect("clientes.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE clientes SET ultimo_cambio_pezoneras = ? WHERE id = ?", (nueva_fecha, id_cliente))

            # Recalcular la fecha de cambio para la columna 5 (Próximo Cambio)
            vacas_item = self.table.item(row_idx, 1)
            ordenes_item = self.table.item(row_idx, 2)
            bajadas_item = self.table.item(row_idx, 3)

            # Validar que los valores no sean None
            if vacas_item is None or ordenes_item is None or bajadas_item is None:
                raise ValueError("Faltan datos para calcular el próximo cambio de pezoneras.")

            vacas = int(vacas_item.text())
            ordenes = int(ordenes_item.text())
            bajadas = int(bajadas_item.text())

            if vacas > 0 and ordenes > 0 and bajadas > 0:
                dias_adicionales = 2500 / (vacas * (ordenes / bajadas))
                dias_adicionales = int(dias_adicionales)
                proximo_cambio = datetime.now() + timedelta(days=dias_adicionales)
                proximo_cambio_str = proximo_cambio.strftime("%Y-%m-%d")

                # Actualizar la columna 5 (Próximo Cambio) en la tabla
                fecha_item = QTableWidgetItem(proximo_cambio_str)
                dias_restantes = (proximo_cambio - datetime.now()).days
                self.colorear_celda(fecha_item, dias_restantes)
                self.table.setItem(row_idx, 5, fecha_item)

                # Guardar el próximo cambio en la base de datos
                cursor.execute("UPDATE clientes SET proximo_cambio_pezoneras = ? WHERE id = ?", (proximo_cambio_str, id_cliente))
            else:
                # Si no se puede calcular el próximo cambio, guardar "Sin datos"
                cursor.execute("UPDATE clientes SET proximo_cambio_pezoneras = ? WHERE id = ?", ("Sin datos", id_cliente))
                self.table.setItem(row_idx, 5, QTableWidgetItem("Sin datos"))

            conn.commit()
            conn.close()

            # Actualizar la columna 4 (Último Cambio de Pezoneras) en la tabla
            nuevo_item = QTableWidgetItem(nueva_fecha)
            nuevo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 4, nuevo_item)

            QMessageBox.information(self, "Éxito", "Cambio de pezoneras registrado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al marcar el cambio: {str(e)}")

    def marcar_cambio_pulsadores(self, id_cliente, row_idx):
        """Marca un cambio de pulsadores para un cliente y actualiza las columnas 10 y 11"""
        try:
            nueva_fecha = datetime.now().strftime("%Y-%m-%d")  # Fecha actual

            # Actualizar la columna 10 (Último Cambio de Pulsador)
            ultimo_cambio_item = QTableWidgetItem(nueva_fecha)
            ultimo_cambio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 10, ultimo_cambio_item)

            # Obtener la fecha de último cambio de pulsador desde la columna 10
            ultimo_cambio_pulsadores_item = self.table.item(row_idx, 10)
            if ultimo_cambio_pulsadores_item is None or ultimo_cambio_pulsadores_item.text() == "Sin datos":
                raise ValueError("La fecha de último cambio de pulsador no es válida.")

            ultimo_cambio_pulsadores = datetime.strptime(ultimo_cambio_pulsadores_item.text(), "%Y-%m-%d")

            # Calcular el próximo cambio (columna 11)
            vacas_item = self.table.item(row_idx, 1)
            vacas = int(vacas_item.text()) if vacas_item else 0
            ordenes = int(self.table.item(row_idx, 2).text())
            bajadas = int(self.table.item(row_idx, 3).text())

            if vacas > 0 and ordenes > 0 and bajadas > 0:
                dias_adicionales = 7000 / (vacas * (ordenes / bajadas))
                dias_adicionales = int(dias_adicionales)
                proximo_cambio = ultimo_cambio_pulsadores + timedelta(days=dias_adicionales)
                proximo_cambio_item = QTableWidgetItem(proximo_cambio.strftime("%Y-%m-%d"))
                dias_restantes = (proximo_cambio - datetime.now()).days
                self.colorear_celda(proximo_cambio_item, dias_restantes)
            else:
                proximo_cambio_item = QTableWidgetItem("Sin datos")

            self.table.setItem(row_idx, 11, proximo_cambio_item)

            # Guardar los cambios en la base de datos
            conn = sqlite3.connect("clientes.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE clientes SET ultimo_cambio_pulsadores = ?, proximo_cambio_pulsadores = ? WHERE id = ?", 
                           (nueva_fecha, proximo_cambio.strftime("%Y-%m-%d"), id_cliente))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Éxito", "Cambio de pulsadores registrado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al marcar el cambio: {str(e)}")

    def marcar_cambio_mangueras(self, id_cliente, row_idx):
        """Marca un cambio de mangueras para un cliente y actualiza las columnas 7 y 8"""
        try:
            # Fecha actual
            nueva_fecha = datetime.now().strftime("%Y-%m-%d")

            # Calcular el próximo cambio de mangueras (6 meses después de la fecha actual)
            proximo_cambio_mangueras = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")

            # Actualizar la columna 7 (Último Cambio de Mangueras)
            fecha_item = QTableWidgetItem(nueva_fecha)
            fecha_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 7, fecha_item)

            # Actualizar la columna 8 (Próximo Cambio de Mangueras)
            proximo_item = QTableWidgetItem(proximo_cambio_mangueras)
            proximo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            dias_restantes = (datetime.strptime(proximo_cambio_mangueras, "%Y-%m-%d") - datetime.now()).days
            self.colorear_celda(proximo_item, dias_restantes)
            self.table.setItem(row_idx, 8, proximo_item)

            # Guardar los cambios en la base de datos
            conn = sqlite3.connect("clientes.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE clientes 
                SET ultimo_cambio = ?, proximo_cambio_mangueras = ? 
                WHERE id = ?
            """, (nueva_fecha, proximo_cambio_mangueras, id_cliente))
            conn.commit()
            conn.close()

            # Mostrar mensaje de éxito
            QMessageBox.information(self, "Éxito", "Cambio de mangueras registrado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al marcar el cambio: {str(e)}")

    def marcar_chequeo(self, id_cliente, row_idx):
        """Marca un chequeo para un cliente y actualiza las columnas 13 y 14"""
        try:
            nueva_fecha = datetime.now().strftime("%Y-%m-%d")  # Fecha actual

            # Actualizar la columna 13 (Fecha de Último Chequeo)
            ultimo_chequeo_item = QTableWidgetItem(nueva_fecha)
            ultimo_chequeo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 13, ultimo_chequeo_item)

            # Calcular el próximo chequeo (columna 14)
            vacas_item = self.table.item(row_idx, 1)
            vacas = int(vacas_item.text()) if vacas_item else 0
            ordenes = int(self.table.item(row_idx, 2).text())
            bajadas = int(self.table.item(row_idx, 3).text())

            if vacas > 0 and ordenes > 0 and bajadas > 0:
                dias_adicionales = 7000 / (vacas * (ordenes / bajadas))
                dias_adicionales = int(dias_adicionales)
                proximo_chequeo = datetime.now() + timedelta(days=dias_adicionales)
                proximo_chequeo_item = QTableWidgetItem(proximo_chequeo.strftime("%Y-%m-%d"))
                dias_restantes = (proximo_chequeo - datetime.now()).days
                self.colorear_celda(proximo_chequeo_item, dias_restantes)
            else:
                proximo_chequeo_item = QTableWidgetItem("Sin datos")

            self.table.setItem(row_idx, 14, proximo_chequeo_item)

            # Guardar los cambios en la base de datos
            conn = sqlite3.connect("clientes.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE clientes SET ultimo_chequeo = ?, proximo_chequeo = ? WHERE id = ?", 
                           (nueva_fecha, proximo_chequeo.strftime("%Y-%m-%d"), id_cliente))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Éxito", "Chequeo registrado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al marcar el chequeo: {str(e)}")

    def delete_cliente(self):
        """Elimina el cliente seleccionado de la base de datos y la tabla"""
        selected_row = self.table.currentRow()  # Obtiene la fila seleccionada en la tabla.
        if selected_row == -1:  # Si no hay ninguna fila seleccionada...
            QMessageBox.warning(self, "Error", "Seleccione un cliente para eliminar.")  # Muestra un mensaje de advertencia.
            return  # Sale de la función.

        cliente_nombre = self.table.item(selected_row, 0).text()  # Obtiene el nombre del cliente de la columna 0.
        confirm = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar al cliente '{cliente_nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )  # Muestra un cuadro de diálogo para confirmar la eliminación.

        if confirm == QMessageBox.StandardButton.Yes:  # Si el usuario confirma la eliminación...
            # Obtener el ID del cliente desde la celda de la tabla
            cliente_id_item = self.table.item(selected_row, 0)
            cliente_id = cliente_id_item.data(Qt.ItemDataRole.UserRole) if cliente_id_item else None

            if cliente_id is None:
                QMessageBox.warning(self, "Error", "No se pudo obtener el ID del cliente.")
                return

            # Eliminar el cliente de la base de datos
            conn = sqlite3.connect("clientes.db")  # Conecta a la base de datos SQLite.
            cursor = conn.cursor()  # Crea un cursor para ejecutar comandos SQL.
            cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))  # Elimina el cliente con el ID dado.
            conn.commit()  # Guarda los cambios en la base de datos.
            conn.close()  # Cierra la conexión con la base de datos.

            # Eliminar la fila correspondiente de la tabla
            self.table.removeRow(selected_row)
            QMessageBox.information(self, "Éxito", f"Cliente '{cliente_nombre}' eliminado correctamente.")

    def calcular_intervalo(self, vacas):
        """Calcula el intervalo de cambio según la cantidad de vacas"""
        if vacas <= 50:
            return 45  # Menos de 50 vacas: 45 días
        elif vacas <= 100:
            return 30  # Entre 51 y 100 vacas: 30 días
        elif vacas > 150:
            return 20  # Más de 150 vacas: 20 días
        else:
            return 30  # Valor por defecto: 30 días

    def select_cliente_para_modificar(self):
        """Permite seleccionar un cliente para modificar su cantidad de vacas"""
        conn = sqlite3.connect("clientes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM clientes")
        clientes = cursor.fetchall()
        conn.close()

        cliente_names = [cliente[1] for cliente in clientes]
        cliente, ok = QInputDialog.getItem(self, "Seleccionar Cliente", "Seleccione un cliente para modificar:",
                                           cliente_names, 0, False)

        if ok and cliente:
            cliente_id = None
            for c in clientes:
                if c[1] == cliente:
                    cliente_id = c[0]
                    break

            if cliente_id is None:
                QMessageBox.warning(self, "Error", "Cliente no encontrado.")
                return

            self.modify_vacas(cliente_id)

    def select_cliente_para_modificar_ordenes(self):
        """Permite seleccionar un cliente para modificar su cantidad de ordeñes"""
        conn = sqlite3.connect("clientes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM clientes")
        clientes = cursor.fetchall()
        conn.close()

        cliente_names = [cliente[1] for cliente in clientes]
        cliente, ok = QInputDialog.getItem(self, "Seleccionar Cliente", "Seleccione un cliente para modificar:",
                                           cliente_names, 0, False)

        if ok and cliente:
            cliente_id = None
            for c in clientes:
                if c[1] == cliente:
                    cliente_id = c[0]
                    break

            if cliente_id is None:
                QMessageBox.warning(self, "Error", "Cliente no encontrado.")
                return

            self.modify_ordenes(cliente_id)

    def select_cliente_para_modificar_bajadas(self):
        """Permite seleccionar un cliente para modificar su cantidad de bajadas"""
        conn = sqlite3.connect("clientes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM clientes")
        clientes = cursor.fetchall()
        conn.close()

        cliente_names = [cliente[1] for cliente in clientes]
        cliente, ok = QInputDialog.getItem(self, "Seleccionar Cliente", "Seleccione un cliente para modificar:",
                                           cliente_names, 0, False)

        if ok and cliente:
            cliente_id = None
            for c in clientes:
                if c[1] == cliente:
                    cliente_id = c[0]
                    break

            if cliente_id is None:
                QMessageBox.warning(self, "Error", "Cliente no encontrado.")
                return

            self.modify_bajadas(cliente_id)

    def modify_vacas(self, cliente_id):
        """Modifica la cantidad de vacas de un cliente y recalcula las ecuaciones dependientes"""
        vacas, ok = QInputDialog.getInt(self, "Modificar Vacas", "Ingrese nueva cantidad de vacas:")

        if ok:
            conn = sqlite3.connect("clientes.db")
            cursor = conn.cursor()

            # Obtener los datos actuales del cliente
            cursor.execute("SELECT ordenes, bajadas, ultimo_cambio_pezoneras, ultimo_cambio_pulsadores FROM clientes WHERE id = ?", (cliente_id,))
            cliente = cursor.fetchone()
            if not cliente:
                QMessageBox.warning(self, "Error", "Cliente no encontrado.")
                conn.close()
                return

            ordenes, bajadas, ultimo_cambio_pezoneras, ultimo_cambio_pulsadores = cliente

            # Recalcular el próximo cambio de pezoneras
            if ultimo_cambio_pezoneras and vacas > 0 and ordenes > 0 and bajadas > 0:
                dias_adicionales_pezoneras = 2500 / (vacas * (ordenes / bajadas))
                fecha_ultimo_cambio_pezoneras = datetime.strptime(ultimo_cambio_pezoneras, "%Y-%m-%d")
                proximo_cambio_pezoneras = (fecha_ultimo_cambio_pezoneras + timedelta(days=int(dias_adicionales_pezoneras))).strftime("%Y-%m-%d")
            else:
                proximo_cambio_pezoneras = "Sin datos"

            # Recalcular el próximo cambio de pulsadores
            if ultimo_cambio_pulsadores and vacas > 0 and ordenes > 0 and bajadas > 0:
                dias_adicionales_pulsadores = 7000 / (vacas * (ordenes / bajadas))
                fecha_ultimo_cambio_pulsadores = datetime.strptime(ultimo_cambio_pulsadores, "%Y-%m-%d")
                proximo_cambio_pulsadores = (fecha_ultimo_cambio_pulsadores + timedelta(days=int(dias_adicionales_pulsadores))).strftime("%Y-%m-%d")
            else:
                proximo_cambio_pulsadores = "Sin datos"

            # Actualizar los datos en la base de datos
            cursor.execute("""
                UPDATE clientes
                SET vacas = ?, proximo_cambio_pezoneras = ?, proximo_cambio_pulsadores = ?
                WHERE id = ?
            """, (vacas, proximo_cambio_pezoneras, proximo_cambio_pulsadores, cliente_id))
            conn.commit()
            conn.close()

            # Recargar los datos en la tabla
            self.load_data()
            QMessageBox.information(self, "Éxito", "Cantidad de vacas actualizada correctamente.")

    def modify_ordenes(self, cliente_id):
        """Modifica la cantidad de ordeñes de un cliente y recalcula los próximos cambios"""
        ordenes, ok = QInputDialog.getInt(self, "Modificar Ordeñes", "Ingrese nueva cantidad de ordeñes:")

        if ok:
            conn = sqlite3.connect("clientes.db")
            cursor = conn.cursor()

            # Obtener los datos actuales del cliente
            cursor.execute("SELECT vacas, bajadas, ultimo_cambio_pezoneras, ultimo_cambio_pulsadores, ultimo_chequeo FROM clientes WHERE id = ?", (cliente_id,))
            cliente = cursor.fetchone()
            if not cliente:
                QMessageBox.warning(self, "Error", "Cliente no encontrado.")
                conn.close()
                return

            vacas, bajadas, ultimo_cambio_pezoneras, ultimo_cambio_pulsadores, ultimo_chequeo = cliente

            # Recalcular el próximo cambio de pezoneras
            if ultimo_cambio_pezoneras and vacas > 0 and ordenes > 0 and bajadas > 0 and ultimo_cambio_pezoneras != "Sin datos":
                dias_adicionales_pezoneras = 2500 / (vacas * (ordenes / bajadas))
                fecha_ultimo_cambio_pezoneras = datetime.strptime(ultimo_cambio_pezoneras, "%Y-%m-%d")
                proximo_cambio_pezoneras = (fecha_ultimo_cambio_pezoneras + timedelta(days=int(dias_adicionales_pezoneras))).strftime("%Y-%m-%d")
            else:
                proximo_cambio_pezoneras = "Sin datos"

            # Recalcular el próximo cambio de pulsadores
            if ultimo_cambio_pulsadores and vacas > 0 and ordenes > 0 and bajadas > 0 and ultimo_cambio_pulsadores != "Sin datos":
                dias_adicionales_pulsadores = 7000 / (vacas * (ordenes / bajadas))
                fecha_ultimo_cambio_pulsadores = datetime.strptime(ultimo_cambio_pulsadores, "%Y-%m-%d")
                proximo_cambio_pulsadores = (fecha_ultimo_cambio_pulsadores + timedelta(days=int(dias_adicionales_pulsadores))).strftime("%Y-%m-%d")
            else:
                proximo_cambio_pulsadores = "Sin datos"

            # Recalcular el próximo chequeo
            if ultimo_chequeo and vacas > 0 and ordenes > 0 and bajadas > 0 and ultimo_chequeo != "Sin datos":
                dias_adicionales_chequeo = 7000 / (vacas * (ordenes / bajadas))
                fecha_ultimo_chequeo = datetime.strptime(ultimo_chequeo, "%Y-%m-%d")
                proximo_chequeo = (fecha_ultimo_chequeo + timedelta(days=int(dias_adicionales_chequeo))).strftime("%Y-%m-%d")
            else:
                proximo_chequeo = "Sin datos"

            # Actualizar los datos en la base de datos
            cursor.execute("""
                UPDATE clientes
                SET ordenes = ?, proximo_cambio_pezoneras = ?, proximo_cambio_pulsadores = ?, proximo_chequeo = ?
                WHERE id = ?
            """, (ordenes, proximo_cambio_pezoneras, proximo_cambio_pulsadores, proximo_chequeo, cliente_id))
            conn.commit()
            conn.close()

            # Recargar los datos en la tabla
            self.load_data()
            QMessageBox.information(self, "Éxito", "Cantidad de ordeñes actualizada correctamente.")

    def modify_bajadas(self, cliente_id):
        """Modifica la cantidad de bajadas de un cliente y recalcula los próximos cambios"""
        bajadas, ok = QInputDialog.getInt(self, "Modificar Bajadas", "Ingrese nueva cantidad de bajadas:")

        if ok:
            conn = sqlite3.connect("clientes.db")
            cursor = conn.cursor()

            # Obtener los datos actuales del cliente
            cursor.execute("SELECT vacas, ordenes, ultimo_cambio_pezoneras, ultimo_cambio_pulsadores, ultimo_chequeo FROM clientes WHERE id = ?", (cliente_id,))
            cliente = cursor.fetchone()
            if not cliente:
                QMessageBox.warning(self, "Error", "Cliente no encontrado.")
                conn.close()
                return

            vacas, ordenes, ultimo_cambio_pezoneras, ultimo_cambio_pulsadores, ultimo_chequeo = cliente

            # Recalcular el próximo cambio de pezoneras
            if ultimo_cambio_pezoneras and vacas > 0 and ordenes > 0 and bajadas > 0 and ultimo_cambio_pezoneras != "Sin datos":
                dias_adicionales_pezoneras = 2500 / (vacas * (ordenes / bajadas))
                fecha_ultimo_cambio_pezoneras = datetime.strptime(ultimo_cambio_pezoneras, "%Y-%m-%d")
                proximo_cambio_pezoneras = (fecha_ultimo_cambio_pezoneras + timedelta(days=int(dias_adicionales_pezoneras))).strftime("%Y-%m-%d")
            else:
                proximo_cambio_pezoneras = "Sin datos"

            # Recalcular el próximo cambio de pulsadores
            if ultimo_cambio_pulsadores and vacas > 0 and ordenes > 0 and bajadas > 0 and ultimo_cambio_pulsadores != "Sin datos":
                dias_adicionales_pulsadores = 7000 / (vacas * (ordenes / bajadas))
                fecha_ultimo_cambio_pulsadores = datetime.strptime(ultimo_cambio_pulsadores, "%Y-%m-%d")
                proximo_cambio_pulsadores = (fecha_ultimo_cambio_pulsadores + timedelta(days=int(dias_adicionales_pulsadores))).strftime("%Y-%m-%d")
            else:
                proximo_cambio_pulsadores = "Sin datos"

            # Recalcular el próximo chequeo
            if ultimo_chequeo and vacas > 0 and ordenes > 0 and bajadas > 0 and ultimo_chequeo != "Sin datos":
                dias_adicionales_chequeo = 7000 / (vacas * (ordenes / bajadas))
                fecha_ultimo_chequeo = datetime.strptime(ultimo_chequeo, "%Y-%m-%d")
                proximo_chequeo = (fecha_ultimo_chequeo + timedelta(days=int(dias_adicionales_chequeo))).strftime("%Y-%m-%d")
            else:
                proximo_chequeo = "Sin datos"

            # Actualizar los datos en la base de datos
            cursor.execute("""
                UPDATE clientes
                SET bajadas = ?, proximo_cambio_pezoneras = ?, proximo_cambio_pulsadores = ?, proximo_chequeo = ?
                WHERE id = ?
            """, (bajadas, proximo_cambio_pezoneras, proximo_cambio_pulsadores, proximo_chequeo, cliente_id))
            conn.commit()
            conn.close()

            # Recargar los datos en la tabla
            self.load_data()
            QMessageBox.information(self, "Éxito", "Cantidad de bajadas actualizada correctamente.")

    def colorear_celda(self, item, dias_restantes):
        """Colorea una celda según los días restantes"""
        if dias_restantes <= 0:
            item.setBackground(QColor("red"))
            item.setForeground(QColor("white"))
        elif dias_restantes <= 15:
            item.setBackground(QColor("orange"))
            item.setForeground(QColor("black"))
        else:
            item.setBackground(QColor("green"))
            item.setForeground(QColor("white"))

    def exit_system(self):
        """Guarda los datos y cierra la aplicación"""
        try:
            self.save_all_data()  # Guarda todos los datos en la base de datos.
            QMessageBox.information(self, "Salir", "Todos los datos han sido guardados correctamente. Cerrando el sistema.")
            self.close()  # Cierra la ventana principal.
            QApplication.quit()  # Cierra la aplicación de PyQt.
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al guardar los datos: {str(e)}")

    def save_all_data(self):
        """Guarda todos los datos de la tabla en la base de datos"""
        conn = sqlite3.connect("clientes.db")
        cursor = conn.cursor()

        for row_idx in range(self.table.rowCount()):
            try:
                # Validar que los elementos existen antes de acceder a ellos
                id_cliente_item = self.table.item(row_idx, 0)
                id_cliente = id_cliente_item.data(Qt.ItemDataRole.UserRole) if id_cliente_item else None

                ultimo_cambio_item = self.table.item(row_idx, 7)
                ultimo_cambio = ultimo_cambio_item.text() if ultimo_cambio_item else "Sin datos"

                proximo_cambio_item = self.table.item(row_idx, 8)
                proximo_cambio_mangueras = proximo_cambio_item.text() if proximo_cambio_item else "Sin datos"

                # Guardar los datos en la base de datos
                cursor.execute("""
                    UPDATE clientes 
                    SET ultimo_cambio = ?, proximo_cambio_mangueras = ? 
                    WHERE id = ?
                """, (ultimo_cambio, proximo_cambio_mangueras, id_cliente))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Ocurrió un error al guardar los datos: {str(e)}")

        conn.commit()
        conn.close()

    def create_marcar_cambio_pezoneras_handler(self, id_cliente, row_idx):
        """Crea un manejador para el botón de marcar cambio de pezoneras"""
        return lambda: self.marcar_cambio_pezoneras(id_cliente, row_idx)

    def create_marcar_cambio_mangueras_handler(self, id_cliente, row_idx):
        """Crea un manejador para el botón de marcar cambio de mangueras"""
        return lambda: self.marcar_cambio_mangueras(id_cliente, row_idx)

    def create_marcar_cambio_pulsadores_handler(self, id_cliente, row_idx):
        """Crea un manejador para el botón de marcar cambio de pulsadores"""
        return lambda: self.marcar_cambio_pulsadores(id_cliente, row_idx)

    def create_marcar_chequeo_handler(self, id_cliente, row_idx):
        """Crea un manejador para el botón de marcar chequeo"""
        return lambda: self.marcar_chequeo(id_cliente, row_idx)

def obtener_version_remota():
    url = "https://raw.githubusercontent.com/Fabrischulz/Control-Tambo/main/version.txt"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return None
    except Exception as e:
        print("Error al verificar versión:", e)
        return None

def descargar_nueva_version():
    url_descarga = "https://github.com/Fabrischulz/Control-Tambo/releases/latest/download/control-tambo.exe"
    nueva_ruta = "nuevo_control_tambo.exe"
    try:
        with requests.get(url_descarga, stream=True, timeout=10) as r:
            with open(nueva_ruta, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        QMessageBox.information(None, "Actualización", f"La nueva versión fue descargada como {nueva_ruta}.\nCierre y reabra la aplicación para usarla.")
    except Exception as e:
        QMessageBox.warning(None, "Error", f"Error al descargar la nueva versión:\n{e}")

def chequear_actualizacion():
    version_remota = obtener_version_remota()
    if version_remota and version_remota != __version__:
        respuesta = QMessageBox.question(
            None,
            "Actualización disponible",
            f"Hay una nueva versión disponible ({version_remota}). ¿Desea descargarla?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            descargar_nueva_version()

if __name__ == "__main__":
    initialize_db()  # Asegura que la base de datos esté configurada correctamente
    app = QApplication(sys.argv)
    window = ClienteApp()
    window.show()
    sys.exit(app.exec())