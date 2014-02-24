import threading
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template
from tornado.options import define, options, parse_command_line

define("port", default=8080, type=int)
define("debug", default=False, type=bool)
define("public_dir", default="public/", type=str)

clients = dict()

texts = {"iliad": "iliad.txt", "conan": "conan.txt"}


class IndexHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	def get(self):
		self.render(options.public_dir + "templates/index.html", texts=texts)


class StreamHandler(tornado.websocket.WebSocketHandler):
	def open(self, *args):
		self.id = self.get_argument("Id")
		self.stream.set_nodelay(True)
		clients[self.id] = {"id": self.id, "object": self}

	def on_message(self, message):
		if message in texts:

			# Repeatedly send part of the full content down to the client
			def send_part(content, index=0):
				if self.id in clients:
					self.write_message(content[index])
					index += 1

					if index < len(content):
						threading.Timer(0.001, send_part, args=[content, index]).start()

			# Open the file and read the content
			fs = open(options.public_dir + "text/" + texts[message])
			send_part(fs.read())

	def on_close(self):
		if self.id in clients:
			del clients[self.id]


if __name__ == '__main__':
	parse_command_line()

	app = tornado.web.Application([
		(r"/", IndexHandler),
		(r"/stream", StreamHandler),
	], debug=options.debug)

	app.listen(options.port)
	print("Listening on port %i" % options.port)
	tornado.ioloop.IOLoop.instance().start()
