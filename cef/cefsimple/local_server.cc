
#include "local_server.h"

#include <iostream>
#include "Poco/PipeStream.h"


LocalServer::LocalServer() : stop(false) {
}

LocalServer::~LocalServer() {
    this->stop_server();
}

void LocalServer::run_server(int port_number, bool persistent) {

    _thread = std::thread(&LocalServer::main, this, port_number, persistent);
}

void LocalServer::stop_server() {
    stop = true;
    if (this->is_running()) {
        Poco::Process::kill(_pid);
    }
    _thread.join();
}

bool LocalServer::is_running() const {
    return Poco::Process::isRunning(_pid);
}

void LocalServer::main(int port_number, bool persistent) {
    std::cout << "LocalServer::main(port_number='" << port_number << "')\n";
    
    // Run server (it will block execution)
    std::string command = "python";
    std::vector<std::string> args;
    args.push_back("test.py");

    Poco::Pipe outPipe;
    Poco::ProcessHandle handler = Poco::Process::launch(command, args, 0, &outPipe, 0);
    Poco::PipeInputStream istr(outPipe);
    _pid = handler.id();
    while(!istr.eof()) {
        std::string data;
        istr >> data;
        std::cout << "OUTPUT: " << data << std::endl;
    }

    handler.wait();
        
    if (false && !stop && persistent) {
        // Rerun server
        this->main(port_number, persistent);
    }
}
