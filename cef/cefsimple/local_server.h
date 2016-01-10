
#pragma once

#include <thread>
#include <Poco/Process.h>

class LocalServer {
    public:
        LocalServer();
        ~LocalServer();
		void cfg_server(const std::string& python, const std::string& manage, std::function<void(const std::string&)>& redirect_to);
        void run_server(bool persistent = true);

        void stop_server();
        bool is_running() const;
    private:
        void main(bool persistent);

		std::string _python;
		std::string _manage;
		std::function<void(const std::string&)> _redirect_to;

		Poco::Process::PID _pid;
        std::thread _thread;
        bool stop;
        
};
