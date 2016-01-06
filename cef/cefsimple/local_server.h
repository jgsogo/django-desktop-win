
#pragma once

#include "include/cef_base.h"
#include <thread>
#include <Poco/Process.h>

class LocalServer : public CefBase {
    public:
        LocalServer();
        ~LocalServer();
        void run_server(int port_number, bool persistent=true);
        void stop_server();
        bool is_running() const;
    private:
        void main(int port_number, bool persistent);

        Poco::Process::PID _pid;
        std::thread _thread;
        bool stop;

        IMPLEMENT_REFCOUNTING(LocalServer);
};
