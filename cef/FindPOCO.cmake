# - finds the Poco C++ libraries
# This module finds the Applied Informatics Poco libraries.
# It supports the following components:
#
# Util (loaded by default)
# Foundation (loaded by default)
# XML
# Zip
# Crypto
# Data
# Net
# NetSSL_OpenSSL
# OSP
#
# Usage:
#	set(ENV{Poco_DIR} path/to/poco/sdk)
#	find_package(Poco REQUIRED OSP Data Crypto) 
#
# On completion, the script defines the following variables:
#	
#	- Compound variables:
#   Poco_FOUND 
#		- true if all requested components were found.
#	Poco_LIBRARIES 
#		- contains release (and debug if available) libraries for all requested components.
#		  It has the form "optimized LIB1 debug LIBd1 optimized LIB2 ...", ready for use with the target_link_libraries command.
#	Poco_INCLUDE_DIRS
#		- Contains include directories for all requested components.
#
#	- Component variables:
#   Poco_Xxx_FOUND 
#		- Where Xxx is the properly cased component name (eg. 'Util', 'OSP'). 
#		  True if a component's library or debug library was found successfully.
#	Poco_Xxx_LIBRARY 
#		- Library for component Xxx.
#	Poco_Xxx_LIBRARY_DEBUG 
#		- debug library for component Xxx
#   Poco_Xxx_INCLUDE_DIR
#		- include directory for component Xxx
#
#  	- OSP BundleCreator variables: (i.e. bundle.exe on windows, bundle on unix-likes)
#		(is only discovered if OSP is a requested component)
#	Poco_OSP_Bundle_EXECUTABLE_FOUND 
#		- true if the bundle-creator executable was found.
#	Poco_OSP_Bundle_EXECUTABLE
#		- the path to the bundle-creator executable.
#
# Author: Andreas Stahl andreas.stahl@tu-dresden.de
# Modified by: Javier G. Sogo

set(Poco_HINTS
	/usr/local
	C:/AppliedInformatics
	${Poco_DIR} 
	$ENV{Poco_DIR}
)

# Determine the project architecture.
if(NOT DEFINED PROJECT_ARCH)
  if(CMAKE_SIZEOF_VOID_P MATCHES 8)
    set(PROJECT_ARCH "x86_64")
  else()
    set(PROJECT_ARCH "x86")
  endif()

  if(OS_MACOSX)
    # PROJECT_ARCH should be specified on Mac OS X.
    message(WARNING "No PROJECT_ARCH value specified, using ${PROJECT_ARCH}")
  endif()
endif()

# Hints to look for libraries and runtime paths, and for runtime names
if(${PROJECT_ARCH} STREQUAL "x86_64")
    set(Poco_LIB_DIR lib64)
    set(Poco_BIN_DIR bin64)
    set(Poco_BIN_SUFFIX "64")
elseif(${PROJECT_ARCH} STREQUAL "x86")
    set(Poco_LIB_DIR lib)
    set(Poco_BIN_DIR bin)
    set(Poco_BIN_SUFFIX "")
else()
    message(ERROR "No PROJECT_ARCH value recognized: ${PROJECT_ARCH}")
endif()


# Library suffixes
if("${CMAKE_CXX_FLAGS_RELEASE} ${CMAKE_CXX_FLAGS_DEBUG}" MATCHES "^(/MT|/MTd)$")
    set(Poco_LIB_SUFFIX "mt")
else()
    set(Poco_LIB_SUFFIX "mt")
endif()



if(NOT Poco_ROOT_DIR)
	# look for the root directory, first for the source-tree variant
	find_path(Poco_ROOT_DIR 
		NAMES Foundation/include/Poco/Poco.h
		HINTS ${Poco_HINTS}
	)
	if(NOT Poco_ROOT_DIR)
		# this means poco may have a different directory structure, maybe it was installed, let's check for that
		message(STATUS "Looking for Poco install directory structure.")
		find_path(Poco_ROOT_DIR 
			NAMES include/Poco/Poco.h
			HINTS ${Poco_HINTS}
		)
		if(NOT Poco_ROOT_DIR) 
			# poco was still not found -> Fail
			if(Poco_FIND_REQUIRED)
				message(FATAL_ERROR "Poco: Could not find Poco install directory")
			endif()
			if(NOT Poco_FIND_QUIETLY)
				message(STATUS "Poco: Could not find Poco install directory")
			endif()
			return()
		else()
			# poco was found with the make install directory structure
			message(STATUS "Assuming Poco install directory structure at ${Poco_ROOT_DIR}.")
			set(Poco_INSTALLED true)
		endif()
	endif()
endif()

# add dynamic library directory
if(WIN32)
	find_path(Poco_RUNTIME_LIBRARY_DIRS
		NAMES PocoFoundation${Poco_BIN_SUFFIX}.dll
		HINTS ${Poco_ROOT_DIR}
		PATH_SUFFIXES 
			${Poco_BIN_DIR}
			${Poco_LIB_DIR}
	)
endif()

# if installed directory structure, set full include dir
if(Poco_INSTALLED)
	set(Poco_INCLUDE_DIRS ${Poco_ROOT_DIR}/include/ CACHE PATH "The global include path for Poco")
endif()

# append the default minimum components to the list to find
list(APPEND components 
	${Poco_FIND_COMPONENTS} 
	# default components:
	"Util" 
	"Foundation"
)
list(REMOVE_DUPLICATES components) # remove duplicate defaults

foreach( component ${components} )
	#if(NOT Poco_${component}_FOUND)
		
	# include directory for the component
	if(NOT Poco_${component}_INCLUDE_DIR)
		find_path(Poco_${component}_INCLUDE_DIR
			NAMES 
				Poco/${component}.h 	# e.g. Foundation.h
				Poco/${component}/${component}.h # e.g. OSP/OSP.h Util/Util.h
			HINTS
				${Poco_ROOT_DIR}
			PATH_SUFFIXES
				include
				${component}/include
		)
	endif()
	if(NOT Poco_${component}_INCLUDE_DIR)
		message(FATAL_ERROR "Poco_${component}_INCLUDE_DIR NOT FOUND")
	else()
		list(APPEND Poco_INCLUDE_DIRS ${Poco_${component}_INCLUDE_DIR})
	endif()

	# release library
	if(NOT Poco_${component}_LIBRARY)
		find_library(
			Poco_${component}_LIBRARY 
			NAMES Poco${component}${Poco_LIB_SUFFIX} 
			HINTS ${Poco_ROOT_DIR}
			PATH_SUFFIXES
				${Poco_LIB_DIR}
				${Poco_BIN_DIR}
		)
		if(Poco_${component}_LIBRARY)
			message(STATUS "Found Poco ${component}: ${Poco_${component}_LIBRARY}")
		endif()
	endif()
	if(Poco_${component}_LIBRARY)
		list(APPEND Poco_LIBRARIES "optimized" ${Poco_${component}_LIBRARY} )
		mark_as_advanced(Poco_${component}_LIBRARY)
	endif()

	# debug library
	if(NOT Poco_${component}_LIBRARY_DEBUG)
		find_library(
			Poco_${component}_LIBRARY_DEBUG
			Names Poco${component}${Poco_LIB_SUFFIX}d
			HINTS ${Poco_ROOT_DIR}
			PATH_SUFFIXES
				${Poco_LIB_DIR}
				${Poco_BIN_DIR}
		)
		if(Poco_${component}_LIBRARY_DEBUG)
			message(STATUS "Found Poco ${component} (debug): ${Poco_${component}_LIBRARY_DEBUG}")
		endif()
	endif(NOT Poco_${component}_LIBRARY_DEBUG)
	if(Poco_${component}_LIBRARY_DEBUG)
		list(APPEND Poco_LIBRARIES "debug" ${Poco_${component}_LIBRARY_DEBUG})
		mark_as_advanced(Poco_${component}_LIBRARY_DEBUG)
	endif()

	# mark component as found or handle not finding it
	if(Poco_${component}_LIBRARY_DEBUG OR Poco_${component}_LIBRARY)
		set(Poco_${component}_FOUND TRUE)
	elseif(NOT Poco_FIND_QUIETLY)
		message(FATAL_ERROR "Could not find Poco component ${component}!")
	endif()
endforeach()

if(DEFINED Poco_LIBRARIES)
	set(Poco_FOUND true)
endif()

if(${Poco_OSP_FOUND})
	# find the osp bundle program
	find_program(
		Poco_OSP_Bundle_EXECUTABLE 
		NAMES bundle
		HINTS 
			${Poco_RUNTIME_LIBRARY_DIRS}
			${Poco_ROOT_DIR}
		PATH_SUFFIXES
			${Poco_BIN_DIR}
			OSP/BundleCreator/${Poco_BIN_DIR}/Darwin/x86_64
			OSP/BundleCreator/${Poco_BIN_DIR}/Darwin/i386
		DOC "The executable that bundles OSP packages according to a .bndlspec specification."
	)
	if(Poco_OSP_Bundle_EXECUTABLE)
		set(Poco_OSP_Bundle_EXECUTABLE_FOUND true)
	endif()
	# include bundle script file
	find_file(Poco_OSP_Bundles_file NAMES PocoBundles.cmake HINTS ${CMAKE_MODULE_PATH})
	if(${Poco_OSP_Bundles_file})
		include(${Poco_OSP_Bundles_file})
	endif()
endif()

message(STATUS "Found Poco: ${Poco_LIBRARIES}")

