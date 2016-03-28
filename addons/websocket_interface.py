"""Module containing some common tools for websocket interaction"""

from BaseHTTPServer import HTTPServer
import os
import socket
from vizhtml import websocket
from SocketServer import ThreadingMixIn
import threading

import viz
import vizact
import vizhtml


_FORM_SUBMIT_EVENT = viz.getEventID('VIZCONNECT_FORM_SUBMIT_EVENT')
_CONNECT_EVENT = viz.getEventID('VIZCONNECT_CONNECT_EVENT')
_MESSAGE_EVENT = viz.getEventID('VIZCONNECT_MESSAGE_EVENT')
_DISCONNECT_EVENT = viz.getEventID('VIZCONNECT_DISCONNECT_EVENT')


class _BaseServerEventHandler(vizhtml.ServerEventHandler):
	"""Base class for handling server events from request thread"""
	
	def onFormSubmit(self, e):
		"""Method to be called when a form is submitted.
		The event object will be passed as the first parameter to the registered function"""
		viz.postEvent(_FORM_SUBMIT_EVENT, e)
	
	def onConnect(self, e):
		"""Method to be called when a WebSocket client has connected to the server.
		The event object will be passed as the first parameter to the registered function"""
		viz.postEvent(_CONNECT_EVENT, e)
	
	def onDisconnect(self, e):
		"""Method to be called when a WebSocket client has disconnected from the server.
		The event object will be passed as the first parameter to the registered function"""
		viz.postFunctionCall(self._disconnectWebSocketClient, e)
	
	def onMessage(self, e):
		"""Method to be called when the specified WebSocket event message is received.
		The event object will be passed as the first parameter to the registered function"""
		viz.postEvent(_MESSAGE_EVENT, e)
	
	def _disconnectWebSocketClient(self, e):
		"""Function that gets called in main thread to trigger disconnect event and notify remove callbacks"""
		viz.sendEvent(_DISCONNECT_EVENT, e)
		e.client._notifyRemoveCallbacks()


def onFormSubmit(func, *args, **kw):
	"""Register a function to be called when a form is submitted.
	The event object will be passed as the first parameter to the registered function"""
	return vizact.onevent(_FORM_SUBMIT_EVENT, lambda e: (True, e), func, *args, **kw)


def onMessage(event, func, *args, **kw):
	"""Register a function to be called when the specified WebSocket event message is received.
	The event object will be passed as the first parameter to the registered function"""
	if event is None:
		return vizact.onevent(_MESSAGE_EVENT, lambda e: (True, e), func, *args, **kw)
	return vizact.onevent(_MESSAGE_EVENT, lambda e: ((e.event == event), e), func, *args, **kw)


def onClientMessage(client, event, func, *args, **kw):
	"""Register a function to be called when the specified WebSocket event message is received from the specified client.
	The event object will be passed as the first parameter to the registered function"""
	if event is None:
		ret = vizact.onevent(_MESSAGE_EVENT, lambda e: ((e.client is client), e), func, *args, **kw)
	else:
		ret = vizact.onevent(_MESSAGE_EVENT, lambda e: ((e.client is client) and (e.event == event), e), func, *args, **kw)
	client.addRemoveCallback(ret.remove)
	return ret


def onConnect(func, *args, **kw):
	"""Register a function to be called when a WebSocket client has connected to the server.
	The event object will be passed as the first parameter to the registered function"""
	return vizact.onevent(_CONNECT_EVENT, lambda e: (True, e), func, *args, **kw)


def onDisconnect(func, *args, **kw):
	"""Register a function to be called when a WebSocket client has disconnected from the server.
	The event object will be passed as the first parameter to the registered function"""
	return vizact.onevent(_DISCONNECT_EVENT, lambda e: (True, e), func, *args, **kw)


def onClientDisconnect(client, func, *args, **kw):
	"""Register a function to be called when the specified WebSocket client has disconnected from the server.
	The event object will be passed as the first parameter to the registered function"""
	ret = vizact.onevent(_DISCONNECT_EVENT, lambda e: ((e.client is client), e), func, *args, **kw)
	client.addRemoveCallback(ret.remove)
	return ret


class ErrorHidingHTTPServer(HTTPServer):
	"""A http server to handle/hide errors"""
	def handle_error(self, request, client_address):
		pass# hidden errors


class _ErrorHidingWebServer(vizhtml.WebServer):
	"""A web server to handle/hide errors"""
	class ErrorHidingThreadedWebServer(ThreadingMixIn, ErrorHidingHTTPServer):
		"""A threaded web server to handle/hide errors"""
		daemon_threads = True
	
	def start(self):
		"""Starts the server and thread"""
		if not self.running:

			# Set running flag
			self.running = True

			# Create HTTP server
			self.server = _ErrorHidingWebServer.ErrorHidingThreadedWebServer((self.context.host, self.context.port), vizhtml.VizardHTTPRequestHandler)
			self.server.context = self.context
			self._updateURL()

			# Start thread for handling server requests
			self.thread = threading.Thread(target=self._serverLoop, args=(self.server, ))
			self.thread.start()


class WebInterface(object):
	"""Websocket-based interface."""
	def __init__(self,
					url,
					baseName,
					resourcePath,
					targetPage=None,
					*args, **kwargs):
		super(WebInterface, self).__init__(*args, **kwargs)
		
		self._url = url.lstrip('/').rstrip('/')
		self._baseName = baseName
		self._resourcePath = resourcePath.rstrip('/')
		self._myEventHandler = _BaseServerEventHandler()
		
		with viz.cluster.MaskedContext(viz.MASTER):
			
			try:
				self._port = vizhtml.getFirstAvailableServerPort(port=9090)
			except socket.error:
				viz.logError('**Error: vizhtml failed to bind to a port.')
				self._port = -1
			
			if self._port > 0:
				self._webServer = _ErrorHidingWebServer(port=self._port)
			
			self._webServer.setEventHandler(self._myEventHandler)
			
			if targetPage is None:
				targetPage = 'index.html'
			# register the vizard code
			if os.path.isdir(self._resourcePath):
				with open(self._resourcePath+"/"+targetPage) as htmlFile:
					self._webServer.registerCode(self._url, htmlFile.read(), directory=self._resourcePath, cache=1000)
			else:
				self._webServer.registerFile(self._url, targetPage, directory=self._resourcePath, cache=1000)
			self._registerCallbacks()
			self._webServer.start()
		
		if self._port:
			self._fullURL = 'http://{}:{}/vizhtml/{}/{}'.format(socket.gethostname(), self._port, self._url, targetPage)
		else:
			self._fullURL = ''
	
	def getURL(self):
		"""Returns the full base URL for the WebInterface object"""
		return self._fullURL
	
	def getWebServer(self):
		"""Returns the webserver object used by this interface.
		
		@return vizhtml.WebServer()
		"""
		return self._webServer
	
	def _onClientConnect(self, e):
		"""Callback triggered when a client connects."""
		pass
	
	def _registerCallbacks(self):
		"""Registers the callbacks triggered by the javascript code in the interface."""
		onConnect(self._onClientConnect)
	
	def _send(self, event, data, client=None):
		"""Send wrapper for convenience"""
		if client is None:
			self._webServer.sendAll(event, data)
		else:
			websocket.sendToAll(event, data, [client])

