# tomcat-ear

The `tomcat-ear` utility enables deployment of Java&copy; Enterprise
Archives (EAR files) into a Tomcat servlet container. It does so by
reading the _Application Deployment Descriptor_ inside the EAR file
(`application.xml`) and then deploying the contained files into the
Tomcat instance in the following way:

- JARs (libraries, EJB modules and application client modules) are
  deployed into one of Tomcat's shared classloaders
- WARs are deployed as ordinary servlet applications
- RARs are not supported

**This does not enable Tomcat to be used as a full-fledged Java EE
server!** It does however enable one specific use-case: the deployment
of a service application implementing shared interfaces for other
servlet applications on the same server.

## Open issues

- library JARs are only added if the `application.xml` contains a
  `library-directory` element.

## Prerequisites
- Python 2.6
- Maven 3
- Tomcat 6 or 7

## Installation

1. clone this repository
2. add `bin/` to your `$PATH`

## Usage

1. set the environment variable `$CATALINA_HOME`, it should point to
   your tomcat directory
2. (optional, but recommended) create a new instance for tomcat and
   set the `$CATALINA_BASE` environment variable
3. execute `tomcat-ear` with an EAR file as it's argument
   
`tomcat-ear` will use the aforementioned environment variables to
learn about where and how the EAR should be deployed.

## Misc

- An example of how to setup Maven for building an EAR is included in
  the `test/examples/` directory.
- You can modify the target directory for the deployment of WEB
  modules by setting the environment variable `$CATALINA_DEPLOY`.

## License

Everything contained inside this directory and it's subdirectories is
subject to the _New BSD License_.
