# Chat Front-End

Web-based chat interface for the ORCA project. It requires the message queue and time server provided in [multi-sensory processing architecture](https://github.com/zedavid/multisensoryprocessing.git), which runs over [FARMI](https://kth.diva-portal.org/smash/get/diva2:1217276/FULLTEXT01.pdf). 

* `chat_interface.py`: Script that launches the client for the web page.

### `templates`

* `layout.html`: pages layout and reference to the js scripts.
* `index.html`: extends `layout.html` and references `chat_window.html` where the contains the box for inputting text and the window displaying the text messages.

### `static/js`

* `chat.js`: has socket that listens to the messages sent from `chat_interface.py` and prints the speech bubbles in the chat window.
* `text-input-event.js`: listens to the key strokes and once enter is pressed sends the text contained in the box to `chat_interface.py`.

NOTE: the current version will answer with an image contained in the `img` folder to anything that is written in the text box.
