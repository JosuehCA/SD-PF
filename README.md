Para crear su entorno virtual, hagan
python -m venv <nombre del entorno>
Yo como nombre suelo utilizar myenv

Después inicien el entorno desde la terminal con:

  Mac: source <path al entorno>/bin/activate
  Windows: .\<path al entorno>\Scripts\activate

Y para instalar las librerías ya dentro del entorno (les sale el símbolo en la terminal si ya están dentro):

  pip install -r requirements.txt

Para salirse del entorno, solo escriban deactivate en la terminal

Si tienen Python a partir del 3.3, venv viene incluido por defecto; si no, hay que instalarlo
