# Planificación de hardware y recursos

La tabla de perfiles del README recoge la escalera de hardware prevista por el proyecto:

- tiny: CPU.
- seed-0: una RTX 4090.
- seed-1: dos A100 de 40 GB.
- seed-2: cuatro A100 de 80 GB.

Son objetivos de planificación. Esta fase inicial no ha medido benchmarks de hardware y no implica garantías de duración, coste ni tokens por segundo.

Antes de ejecutar un perfil distinto de tiny, se debe elaborar un informe de adecuación específico de la máquina que incluya:

- modelo y número de GPU, VRAM, versiones de controlador y CUDA;
- recuento exacto de parámetros y tipo numérico;
- tamaño del micro-lote, longitud de secuencia y acumulación de gradientes;
- memoria estimada y medida de parámetros, gradientes, optimizador y activaciones;
- implementación de atención y asignaciones temporales máximas;
- rendimiento de CPU, RAM y almacenamiento del cargador de datos;
- tiempo de paso medido, tokens por segundo y utilización;
- tamaño del checkpoint, tiempo de escritura y espacio libre en disco.

Que los parámetros quepan en memoria no garantiza que el paso hacia delante y hacia atrás vaya a completarse: también cuentan las activaciones, estados del optimizador, espacios de trabajo temporales, fragmentación y búferes de comunicación. La implementación actual todavía no ofrece un estimador de adecuación al hardware validado. No se debe decidir el lanzamiento usando únicamente cálculos aproximados del número de parámetros.
