
#include "local_server.h"

#include <iostream>
#include "Poco/PipeStream.h"

#include "include/base/cef_logging.h"

LocalServer::LocalServer() : stop(false) {
}

LocalServer::~LocalServer() {
    this->stop_server();
}

void LocalServer::cfg_server(const std::string& python, const std::string& manage, std::function<void(const std::string&)>& redirect_to) {
	_redirect_to = redirect_to;
	_python = python;
	_manage = manage;
}

void LocalServer::run_server(bool persistent) {
    _thread = std::thread(&LocalServer::main, this, persistent);
}

void LocalServer::stop_server() {
    stop = true;
	if (_pid != -1) {
		if (this->is_running()) {
			//Poco::Process::requestTermination(_pid);
			Poco::Process::kill(_pid);
		}
		_thread.join();
	}
}

bool LocalServer::is_running() const {
	return Poco::Process::isRunning(_pid);
}

void LocalServer::main(bool persistent) {
	// Run server (it will block execution)
    std::string command = "\"" + _python + "\"";;
    std::vector<std::string> args;
	args.push_back("\"" + _manage + "\"");
	args.push_back("runserver");

    Poco::Pipe outPipe;
    Poco::ProcessHandle handler = Poco::Process::launch(command, args, 0, &outPipe, 0);
    Poco::PipeInputStream istr(outPipe);
    _pid = handler.id();

	while(!istr.eof()) {
		std::string data;
        istr >> data;
		if (data.find("http://") != std::string::npos) {
			_redirect_to(data);
		}
    }

    handler.wait();
        
    if (false && !stop && persistent) {
        // Rerun server
        this->main(persistent);
    }
}
