
#pragma once

#include "include/cef_base.h"
#include <thread>
#include <Poco/Process.h>

class LocalServer : public CefBase {
    public:
        LocalServer();
        ~LocalServer();
        void run_server(const std::string& python, const std::string& manage, bool persistent=true);
        void stop_server();
        bool is_running() const;
    private:
        void main(bool persistent);

		std::string _python;
		std::string _manage;
		Poco::Process::PID _pid;
        std::thread _thread;
        bool stop;

        IMPLEMENT_REFCOUNTING(LocalServer);
};
