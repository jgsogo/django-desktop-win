// Copyright (c) 2013 The Chromium Embedded Framework Authors. All rights
// reserved. Use of this source code is governed by a BSD-style license that
// can be found in the LICENSE file.

#include "cefsimple/simple_app.h"

#include <string>

#include "cefsimple/simple_handler.h"
#include "include/cef_browser.h"
#include "include/cef_command_line.h"
#include "include/wrapper/cef_helpers.h"

SimpleApp::SimpleApp() : _home_url("/") {

}

void SimpleApp::OnContextInitialized() {
  CEF_REQUIRE_UI_THREAD();

  // Information used when creating the native window.
  CefWindowInfo window_info;

#if defined(OS_WIN)
  // On Windows we need to specify certain flags that will be passed to
  // CreateWindowEx().
  window_info.SetAsPopup(NULL, "cefsimple");
#endif

  // SimpleHandler implements browser-level callbacks.
  CefRefPtr<SimpleHandler> handler(new SimpleHandler());

  // Specify CEF browser settings here.
  CefBrowserSettings browser_settings;

  // Create the first browser window.  
  CefBrowserHost::CreateBrowserSync(window_info, handler.get(), "http://google.com/",
									browser_settings, NULL);
  
  // Configure server
  CefRefPtr<CefCommandLine> command_line = CefCommandLine::GetGlobalCommandLine();
  std::string python = command_line->GetSwitchValue("python");
  std::string manage = command_line->GetSwitchValue("manage");
  if (command_line->HasSwitch("url")) {
	  _home_url = command_line->GetSwitchValue("url");
  }
  std::function<void(const std::string&)> f = [this](const std::string& url) {this->server_base(url);};
  _server.cfg_server(python, manage, f);
  _server.run_server();
}

void SimpleApp::server_base(const std::string& base_url) {
	std::string url = base_url + _home_url;
	CefRefPtr<SimpleHandler> handler(SimpleHandler::GetInstance());
	handler->set_main_url(url);
}