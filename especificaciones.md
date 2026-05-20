# Universidad de Costa Rica

Facultad de Ingeniería  
Escuela de Ciencias de la Computación e Informática  
Bachillerato en Ingeniería en Computación

**Bases de Datos Avanzadas CI-0141**

## Especificación del Proyecto Programado

**Cliente Integrado de Motores de Bases de Datos Distribuidas con Soporte de Consultas, Bitácora y Recuperación ante Fallos**

Profesor: Ing. Sleyter Angulo Chavarría, M.Sc.  
I Ciclo 2026

---

## 1. Generalidades

- **Trabajo en grupos:** Los grupos serán los mismos definidos al inicio del ciclo lectivo.
- **Integridad académica:** El uso de herramientas de inteligencia artificial o la copia de código sin la referencia explícita correspondiente constituye fraude académico y será tratado con las sanciones que establece el Reglamento de la Universidad de Costa Rica.
- **Rubro:** Este proyecto equivale al 20% del rubro de proyectos del curso.

## 2. Objetivo General

Diseñar e implementar un cliente propio de bases de datos distribuidas que permita conectarse a múltiples motores de bases de datos (relacionales y NoSQL), ejecutar consultas sobre ellos, mantener una bitácora transaccional y simular los principales protocolos de recuperación ante fallos utilizados en los Sistemas Gestores de Bases de Datos (SGBD).

## 3. Objetivos Específicos

- Desarrollar un cliente con interfaz gráfica o de línea de comandos capaz de conectarse, de forma simultánea o alternada, a al menos dos motores de bases de datos de distinta naturaleza (p. ej. uno relacional y uno NoSQL).
- Permitir la ejecución de consultas (lectura, inserción, actualización y eliminación) sobre cada motor conectado.
- Implementar un módulo de bitácora (Write-Ahead Log, WAL) que registre las operaciones ejecutadas por cada transacción.
- Simular los cuatro protocolos de recuperación ante fallos: No-Undo/No-Redo, No-Undo/Redo, Undo/No-Redo y Undo/Redo.
- Permitir al usuario forzar fallos controlados y demostrar el proceso de recuperación con cada protocolo.
- Documentar el diseño, las decisiones técnicas y el análisis comparativo de los protocolos en un informe LaTeX.

## 4. Descripción General del Proyecto

El sistema funcionará como un cliente unificado que puede conectarse a distintos nodos de bases de datos distribuidas —tanto relacionales como NoSQL— y ejecutar operaciones sobre ellos de manera transparente para el usuario. Adicionalmente, el sistema deberá registrar cada operación en una bitácora y ofrecer mecanismos de recuperación ante fallos basados en los cuatro protocolos estudiados en clase.

### 4.1 Componentes Principales

#### 4.1.1 Módulo de Conexión Multi-Motor

- Permite al usuario registrar conexiones a distintos motores de bases de datos.
- Soporta al menos un motor relacional (p. ej. MySQL, PostgreSQL, MariaDB) y al menos un motor NoSQL (p. ej. MongoDB, Redis, Cassandra).
- Gestiona las credenciales y el estado de cada conexión (activa/inactiva).
- Permite cambiar de motor durante la sesión sin reiniciar la aplicación.

#### 4.1.2 Módulo de Ejecución de Consultas

- Proporciona una interfaz para escribir y enviar consultas al motor activo.
- Muestra los resultados de forma tabular o estructurada (JSON para NoSQL).
- Soporta transacciones explícitas: BEGIN, COMMIT y ROLLBACK.
- Registra cada operación en la bitácora antes de ejecutarla (Write-Ahead Log).

#### 4.1.3 Módulo de Bitácora (Write-Ahead Log)

- Registra, por cada transacción, las operaciones ejecutadas con la siguiente información:
  - Identificador de transacción (TID).
  - Tipo de operación (INSERT, UPDATE, DELETE, COMMIT, ABORT).
  - Valores anteriores (before image) y nuevos (after image) de los datos modificados.
  - Marca de tiempo (timestamp).
  - Motor de base de datos destino.
- La bitácora se almacena de forma persistente (archivo o base de datos auxiliar).
- Se visualiza en la interfaz del cliente con filtros por transacción, operación y tiempo.

#### 4.1.4 Módulo de Recuperación ante Fallos

El sistema debe implementar y simular los cuatro protocolos de recuperación ante fallos. La Tabla 1 describe cada uno:

**Tabla 1: Protocolos de recuperación ante fallos implementados**

| Protocolo               | UNDO | REDO | Descripción                                                                                                |
|-------------------------|------|------|------------------------------------------------------------------------------------------------------------|
| No-Undo / No-Redo       | No   | No   | Las páginas modificadas no se escriben en disco hasta que la transacción finalice (fuerza escritura al commit). |
| No-Undo / Redo          | No   | Sí   | Los cambios se escriben en disco antes del commit; se necesita REDO si hay fallo tras el commit.             |
| Undo / No-Redo          | Sí   | No   | Las páginas modificadas pueden escribirse en cualquier momento; se requiere UNDO si la transacción aborta.   |
| Undo / Redo             | Sí   | Sí   | Política más flexible: las páginas pueden escribirse en cualquier momento y se aplica UNDO/REDO según sea necesario. |

Para cada protocolo, el sistema deberá:

- Permitir al usuario seleccionar el protocolo activo antes de iniciar una transacción.
- Simular un fallo controlado (p. ej. abortar la transacción en un punto arbitrario).
- Ejecutar el proceso de recuperación correspondiente consultando la bitácora.
- Mostrar el estado de los datos antes y después de la recuperación.

#### 4.1.5 Interfaz de Usuario

- Puede ser gráfica (GUI de escritorio o aplicación web) o de línea de comandos interactiva (TUI/CLI).
- Permite gestionar conexiones, ejecutar consultas, visualizar la bitácora y disparar simulaciones de fallos.
- Muestra el protocolo de recuperación activo y el estado de las transacciones en curso.

### 4.2 Prototipo de Baja Fidelidad

(Ya se hizo el cliente en React)

## 5. Requisitos del Sistema

Los siguientes requisitos representan el mínimo esperado que el sistema debe cumplir. Los grupos son libres —y se incentiva— a ir más allá de este conjunto base, incorporando características adicionales que enriquezcan la solución. La calidad y el alcance serán tomados en cuenta durante la evaluación.

### 5.1 Requisitos Funcionales (mínimos)

- **RF-01:** El cliente debe poder conectarse a al menos dos motores de bases de datos de naturaleza diferente de forma simultánea.
- **RF-02:** El cliente debe permitir ejecutar operaciones CRUD sobre cada motor conectado.
- **RF-03:** El cliente debe soportar transacciones explícitas (BEGIN, COMMIT, ROLLBACK).
- **RF-04:** Toda operación de escritura debe quedar registrada en la bitácora antes de ser aplicada a la base de datos (WAL).
- **RF-05:** El sistema debe implementar los cuatro protocolos de recuperación: No-Undo/No-Redo, No-Undo/Redo, Undo/No-Redo y Undo/Redo.
- **RF-06:** El usuario debe poder seleccionar el protocolo de recuperación activo para cada sesión de transacción.
- **RF-07:** El sistema debe permitir simular fallos y demostrar el proceso de recuperación utilizando la bitácora.
- **RF-08:** La bitácora debe ser consultable desde la interfaz con al menos dos filtros (p. ej. TID y rango de tiempo).

### 5.2 Requisitos No Funcionales (mínimos)

- **RNF-01:** El sistema debe tolerar la desconexión de un nodo sin que el cliente se cierre inesperadamente.
- **RNF-02:** La bitácora debe sobrevivir a reinicios del cliente (persistencia).
- **RNF-03:** El código fuente debe estar versionado en un repositorio Git con al menos una rama de trabajo por integrante.
- **RNF-04:** El README del repositorio debe incluir instrucciones claras de configuración y ejecución.

## 6. Tecnologías Sugeridas

La Tabla 2 presenta las tecnologías recomendadas para cada componente del sistema.

**Tabla 2: Tecnologías sugeridas por categoría**

| Categoría                 | Opciones sugeridas                                               |
|---------------------------|------------------------------------------------------------------|
| Lenguaje principal        | Python / Java / Node.js / Go                                    |
| Motores relacionales      | MySQL, PostgreSQL, MariaDB                                      |
| Motores NoSQL             | MongoDB, Redis, Cassandra, CouchDB                              |
| Orquestación de nodos     | Docker Compose (para simular nodos distribuidos)                |
| Framework de interfaz     | Flask, FastAPI, React, Electron, JavaFX                         |
| Repositorio de código     | GitHub, GitLab, Bitbucket, Git ECCI                             |
| Gestión de tareas         | Jira, GitHub Projects, Trello                                   |

**Nota:** Se recomienda usar Docker Compose para levantar los nodos de bases de datos de manera reproducible y facilitar la evaluación del proyecto.

## 7. Entregables

- **Código fuente:** Repositorio Git con el código completo del cliente, instrucciones de instalación y archivo de configuración de Docker Compose (si aplica).
- **Informe LaTeX:** Documento PDF compilado desde LaTeX con al menos las siguientes secciones:
  - Introducción y motivación.
  - Descripción de la arquitectura del cliente.
  - Análisis de los cuatro protocolos de recuperación implementados.
  - Diseño e implementación de la bitácora.
  - Resultados de las simulaciones de fallos.
  - Conclusiones y reflexiones.
  - Referencias bibliográficas.
- **Diagramas:** Incluidos en el informe LaTeX y en el repositorio (formato editable preferido). Debe haber al menos:
  - Diagrama de arquitectura general del cliente.
  - Diagrama de flujo del proceso de recuperación para cada protocolo.
  - Diagrama de la estructura de la bitácora.
- **Presentación oral:** Demostración en vivo del sistema funcionando con al menos una simulación de fallo y recuperación por cada protocolo.

## 8. Criterio de Evaluación

La Tabla 3 describe los criterios y la ponderación para la evaluación del proyecto. Este proyecto equivale al 20% del rubro de proyectos del curso.

**Tabla 3: Criterios de evaluación**

| Rubro                         | Descripción general                                                                                           | Puntos |
|-------------------------------|---------------------------------------------------------------------------------------------------------------|--------|
| Documentación (LaTeX)         | Informe técnico completo en LaTeX: introducción, diseño, análisis de protocolos de recuperación, conclusiones y referencias. | 20 pts |
| Diagramas                     | Diagramas de arquitectura, flujo de recuperación por protocolo y topología de nodos distribuidos.               | 10 pts |
| Código e Implementación       | Corrección, modularidad, conexión multi-motor, ejecución de consultas, bitácora y simulación de los cuatro protocolos de recuperación. | 50 pts |
| Presentación                  | Exposición oral clara, demostración en vivo del cliente, capacidad de respuesta ante preguntas técnicas.       | 20 pts |
| **TOTAL**                     |                                                                                                               | **100 pts** |

### 8.1 Desglose: Código e Implementación (50 pts)

| Aspecto evaluado                                                               | Puntos |
|--------------------------------------------------------------------------------|--------|
| Conexión y gestión de múltiples motores (≥ 2 motores distintos)               | 10 pts |
| Ejecución de consultas CRUD y soporte de transacciones                        | 10 pts |
| Implementación correcta de la bitácora (WAL, persistencia, visualización)     | 10 pts |
| Implementación de los 4 protocolos de recuperación ante fallos                | 15 pts |
| Calidad del código: modularidad, legibilidad y buenas prácticas               | 5 pts  |
| **SUBTOTAL**                                                                   | **50 pts** |

## 9. Herramientas

- **Repositorio Git:** Bitbucket, GitHub, GitLab o Git ECCI.
- **Manejador de tareas:** Jira, GitHub Projects, Trello u otro.
- **IDE:** VS Code, IntelliJ, PyCharm u otro de preferencia del grupo.
- **Contenedores:** Docker y Docker Compose para levantar los nodos de bases de datos.
- **Redacción del informe:** LaTeX (Overleaf o instalación local).

## 10. Fechas Importantes y Notas

### 10.1 Fechas de Entrega

| Evento                                                              | Fecha y hora                     |
|---------------------------------------------------------------------|----------------------------------|
| Entrega del proyecto (código + informe + diagramas en repositorio)  | Domingo 24 de mayo de 2026 — 23:55 |
| Presentación oral y demostración en vivo (defensa del proyecto)     | Lunes 25 de mayo de 2026 — desde las 07:00 |

**Nota sobre la presentación:** Cada grupo realizará una demostración en vivo del sistema funcionando, incluyendo al menos una simulación de fallo y recuperación para cada uno de los cuatro protocolos implementados. Todos los integrantes deberán estar en capacidad de responder preguntas técnicas sobre cualquier parte del proyecto.

### 10.2 Otras notas

- No se aceptarán proyectos entregados fuera del plazo, salvo con justificación formal presentada ante la Escuela.
- Todos los integrantes deben tener commits en el repositorio; la ausencia de aportes verificables puede implicar nota cero para ese integrante.
- El informe debe compilar correctamente desde el archivo `.tex` sin modificaciones manuales al PDF.

## 11. Enunciado de Honor

El trabajo realizado en este proyecto será el resultado de mi propio esfuerzo y el de mis compañeros de grupo. No usaré, recibiré ni ofreceré ayuda no autorizada. No copiaré de otros proyectos, no utilizaré código publicado en internet sin su debida referencia, ni permitiré que nadie copie parte alguna de este proyecto. No realizaré ninguna trampa ni procedimiento deshonesto en la realización de este trabajo.

Al hacer entrega de cualquier parte de este proyecto, lo hago bajo fe de juramento de cumplir con el presente enunciado de honor.

*Firma y nombre del integrante*