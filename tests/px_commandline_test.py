# coding=utf-8

import os

from px import px_commandline


def test_get_command_python():
    assert px_commandline.get_command("python") == "python"
    assert px_commandline.get_command("/apa/Python") == "Python"
    assert px_commandline.get_command("python --help") == "python"

    # These are inspired by Python 2.7.11 --help output
    assert px_commandline.get_command("python apa.py") == "apa.py"
    assert px_commandline.get_command("python /usr/bin/apa.py") == "apa.py"
    assert px_commandline.get_command("python2.7 /usr/bin/apa.py") == "apa.py"
    assert px_commandline.get_command("python /usr/bin/hej") == "hej"
    assert px_commandline.get_command("python /usr/bin/hej gris --flaska") == "hej"
    assert px_commandline.get_command("python -c cmd") == "python"
    assert px_commandline.get_command("python -m mod") == "mod"
    assert px_commandline.get_command("python -m mod --hej gris --frukt") == "mod"
    assert px_commandline.get_command("Python -") == "Python"

    # Ignoring switches
    assert px_commandline.get_command("python -E apa.py") == "apa.py"
    assert px_commandline.get_command("python3 -E") == "python3"
    assert px_commandline.get_command("python -u -t -m mod") == "mod"

    # -W switches unsupported for now, room for future improvement
    assert px_commandline.get_command("python -W warning:spec apa.py") == "python"

    # Invalid command lines
    assert px_commandline.get_command("python -W") == "python"
    assert px_commandline.get_command("python -c") == "python"
    assert px_commandline.get_command("python -m") == "python"
    assert px_commandline.get_command("python -m   ") == "python"
    assert px_commandline.get_command("python -m -u") == "python"
    assert px_commandline.get_command("python    ") == "python"


def test_get_command_java():
    assert px_commandline.get_command("java") == "java"
    assert px_commandline.get_command("java -version") == "java"
    assert px_commandline.get_command("java -help") == "java"

    assert px_commandline.get_command("java SomeClass") == "SomeClass"
    assert px_commandline.get_command("java x.y.SomeClass") == "SomeClass"
    assert px_commandline.get_command("java -jar flaska.jar") == "flaska.jar"
    assert px_commandline.get_command("java -jar /a/b/flaska.jar") == "flaska.jar"

    # Special handling of class name "Main"
    assert px_commandline.get_command("java a.b.c.Main") == "c.Main"

    # We should ignore certain command line parameters
    assert px_commandline.get_command("java -server SomeClass") == "SomeClass"
    assert px_commandline.get_command("java -Xwhatever SomeClass") == "SomeClass"
    assert px_commandline.get_command("java -Dwhatever SomeClass") == "SomeClass"
    assert px_commandline.get_command("java -cp /a/b/c SomeClass") == "SomeClass"
    assert px_commandline.get_command("java -classpath /a/b/c SomeClass") == "SomeClass"
    assert px_commandline.get_command("java -eahej SomeClass") == "SomeClass"
    assert px_commandline.get_command("java -dahej SomeClass") == "SomeClass"

    # Tests for invalid command lines
    assert px_commandline.get_command("java -cp /a/b/c") == "java"
    assert px_commandline.get_command("java  ") == "java"
    assert px_commandline.get_command("java -jar") == "java"
    assert px_commandline.get_command("java -jar    ") == "java"

    # FIXME: Add test for classpath containing spaces? I say this should be
    # postponed until we have a real world use case for that.
    pass


def test_get_command_java_gradled():
    commandline = (
        "/Library/Java/JavaVirtualMachines/jdk1.8.0_60.jdk/Contents/Home/bin/java " +
        "-XX:MaxPermSize=256m -XX:+HeapDumpOnOutOfMemoryError -Xmx1024m " +
        "-Dfile.encoding=UTF-8 -Duser.country=SE -Duser.language=sv -Duser.variant -cp " +
        "/Users/johan/.gradle/wrapper/dists/gradle-2.8-all/gradle-2.8/lib/gradle-launcher-2.8.jar" +
        " org.gradle.launcher.daemon.bootstrap.GradleDaemon 2.8")
    assert px_commandline.get_command(commandline) == "GradleDaemon"


def test_get_command_java_teamcity():
    commandline = (
        "/usr/lib/jvm/jdk-8-oracle-x64/jre/bin/java " +
        "-Djava.util.logging.config.file=/teamcity/conf/logging.properties " +
        "-Djava.util.logging.manager=org.apache.juli.ClassLoaderLogManager " +
        "-Dsun.net.inetaddr.ttl=60 -server -Xms31g -Xmx31g " +
        "-Dteamcity.configuration.path=../conf/teamcity-startup.properties " +
        "-Dlog4j.configuration=file:/teamcity/bin/../conf/teamcity-server-log4j.xml " +
        "-Dteamcity_logs=../logs/ -Djsse.enableSNIExtension=false -Djava.awt.headless=true " +
        "-Djava.endorsed.dirs=/teamcity/endorsed " +
        "-classpath /teamcity/bin/bootstrap.jar:/teamcity/bin/tomcat-juli.jar " +
        "-Dcatalina.base=/teamcity -Dcatalina.home=/teamcity " +
        "-Djava.io.tmpdir=/teamcity/temp org.apache.catalina.startup.Bootstrap start")
    assert px_commandline.get_command(commandline) == "Bootstrap"


def test_get_command_java_logstash():
    # From: https://github.com/elastic/logstash/issues/3315
    commandline = (
        "/usr/bin/java -XX:+UseParNewGC -XX:+UseConcMarkSweepGC " +
        "-Djava.awt.headless=true -XX:CMSInitiatingOccupancyFraction=75 " +
        "-XX:+UseCMSInitiatingOccupancyOnly -Djava.io.tmpdir=/var/lib/logstash " +
        "-Xmx128m -Xss2048k -Djffi.boot.library.path=/opt/logstash/vendor/jruby/lib/jni " +
        "-XX:+UseParNewGC -XX:+UseConcMarkSweepGC -Djava.awt.headless=true " +
        "-XX:CMSInitiatingOccupancyFraction=75 -XX:+UseCMSInitiatingOccupancyOnly " +
        "-Djava.io.tmpdir=/var/lib/logstash " +
        "-Xbootclasspath/a:/opt/logstash/vendor/jruby/lib/jruby.jar -classpath : " +
        "-Djruby.home=/opt/logstash/vendor/jruby " +
        "-Djruby.lib=/opt/logstash/vendor/jruby/lib -Djruby.script=jruby " +
        "-Djruby.shell=/bin/sh org.jruby.Main --1.9 /opt/logstash/lib/bootstrap/environment.rb " +
        "logstash/runner.rb agent -f /etc/logstash/conf.d -l /var/log/logstash/logstash.log")
    assert px_commandline.get_command(commandline) == "jruby.Main"


def test_get_command_java_gradleworkermain():
    commandline = (
        "/some/path/bin/java "
        "-Djava.awt.headless=true "
        "-Djava.security.manager="
        + "worker.org.gradle.process.internal.worker.child.BootstrapSecurityManager "
        "-Dorg.gradle.native=false "
        "-Drobolectric.accessibility.enablechecks=true "
        "-Drobolectric.logging=stderr "
        "-Drobolectric.logging.enabled=true "
        "-agentlib:jdwp=transport=dt_socket,server=y,address=,suspend=n "
        "-noverify "
        "-javaagent:gen_build/.../jacocoagent.jar="
        + "destfile=gen_build/jacoco/testDebugUnitTest.exec,"
        + "append=true,dumponexit=true,output=file,jmx=false "
        "-Xmx2400m "
        "-Dfile.encoding=UTF-8 "
        "-Duser.country=SE "
        "-Duser.language=sv "
        "-Duser.variant "
        "-ea "
        "-cp "
        "/Users/walles/.gradle/caches/4.2.1/workerMain/gradle-worker.jar "
        "worker.org.gradle.process.internal.worker.GradleWorkerMain "
        "'Gradle Test Executor 16'"
    )
    assert px_commandline.get_command(commandline) == "GradleWorkerMain"


def test_get_command_java_equinox():
    # You get these processes with Visual Studio Code's java environment in October 2020
    commandline = (
        "/Library/Java/JavaVirtualMachines/openjdk-11.jdk/Contents/Home/bin/java "
        "--add-modules=ALL-SYSTEM "
        "--add-opens "
        "java.base/java.util=ALL-UNNAMED "
        "--add-opens "
        "java.base/java.lang=ALL-UNNAMED "
        "-Declipse.application=org.eclipse.jdt.ls.core.id1 "
        "-Dosgi.bundles.defaultStartLevel=4 "
        "-Declipse.product=org.eclipse.jdt.ls.core.product "
        "-Dfile.encoding=utf8 "
        "-XX:+UseParallelGC "
        "-XX:GCTimeRatio=4 "
        "-XX:AdaptiveSizePolicyWeight=90 "
        "-Dsun.zip.disableMemoryMapping=true "
        "-Xmx1G "
        "-Xms100m "
        "-noverify "
        "-jar "
        "/Users/walles/.vscode/extensions/redhat.java-0.68.0/server/plugins/org.eclipse.equinox.launcher_1.5.800.v20200727-1323.jar "
        "-configuration "
        "/Users/walles/Library/Application "
        "Support/Code/User/globalStorage/redhat.java/0.68.0/config_mac "
        "-data "
        "/Users/walles/Library/Application "
        "Support/Code/User/workspaceStorage/b8c3a38f62ce0fc92ce4edfb836480db/redhat.java/jdt_ws "
    )
    assert px_commandline.get_command(commandline) == "org.eclipse.equinox.launcher_1.5.800.v20200727-1323.jar"


def test_get_command_resque():
    # These command names are from a real-world system
    assert px_commandline.get_command("resque-1.20.0: x y z") == "resque-1.20.0:"
    assert px_commandline.get_command("resqued-0.7.12 a b c") == "resqued-0.7.12"


def test_get_command_sudo():
    assert px_commandline.get_command("sudo") == "sudo"
    assert px_commandline.get_command("sudo python /usr/bin/hej gris --flaska") == "sudo hej"

    # We could support flags at some point, but until proven necessary we'll
    # fall back on just "sudo" when we get flags.
    assert px_commandline.get_command("sudo -B python /usr/bin/hej") == "sudo"


def test_get_command_sudo_with_space_in_command_name(tmpdir):
    # Create a file name with a space in it
    spaced_path = tmpdir.join("i contain spaces")
    spaced_path.write_binary(b"")
    spaced_name = str(spaced_path)

    # Verify splitting of the spaced file name
    assert px_commandline.get_command("sudo " + spaced_name) == "sudo i contain spaces"

    # Verify splitting with more parameters on the line
    assert px_commandline.get_command("sudo " + spaced_name + " parameter") == \
        "sudo i contain spaces"


def test_get_command_sudo_with_space_in_path(tmpdir):
    # Create a file name with a space in it
    spaced_dir = tmpdir.join("i contain spaces")
    os.mkdir(str(spaced_dir))
    spaced_path = spaced_dir + "/runme"

    spaced_path.write_binary(b"")
    spaced_name = str(spaced_path)

    # Verify splitting of the spaced file name
    assert px_commandline.get_command("sudo " + spaced_name) == "sudo runme"

    # Verify splitting with more parameters on the line
    assert px_commandline.get_command("sudo " + spaced_name + " parameter") == "sudo runme"


def test_get_command_interpreters():
    assert px_commandline.get_command("ruby") == "ruby"
    assert px_commandline.get_command("ruby /some/path/apa.rb") == "apa.rb"
    assert px_commandline.get_command("ruby -option /some/path/apa.rb") == "ruby"

    assert px_commandline.get_command("sh") == "sh"
    assert px_commandline.get_command("sh /some/path/apa.sh") == "apa.sh"
    assert px_commandline.get_command("sh -option /some/path/apa.sh") == "sh"

    assert px_commandline.get_command("bash") == "bash"
    assert px_commandline.get_command("bash /some/path/apa.sh") == "apa.sh"
    assert px_commandline.get_command("bash -option /some/path/apa.sh") == "bash"

    assert px_commandline.get_command("perl") == "perl"
    assert px_commandline.get_command("perl /some/path/apa.pl") == "apa.pl"
    assert px_commandline.get_command("perl -option /some/path/apa.pl") == "perl"


def test_get_command_unicode():
    assert px_commandline.get_command(u"😀") == u"😀"


def test_get_command_ruby_switches():
    assert px_commandline.get_command(
        "/usr/bin/ruby -W0 /usr/local/bin/brew.rb install rust") == "brew.rb"


def test_get_homebrew_commandline():
    # Source: https://github.com/walles/px/issues/72
    assert px_commandline.get_command(" ".join([
        "/usr/local/Homebrew/Library/Homebrew/vendor/portable-ruby/current/bin/ruby",
        "-W0",
        "--disable=gems,did_you_mean,rubyopt",
        "/usr/local/Homebrew/Library/Homebrew/brew.rb",
        "upgrade"
    ])) == "brew.rb"


def test_node_max_old_space():
    assert px_commandline.get_command(
        "node --max_old_space_size=4096 scripts/start.js") == "start.js"


def test_macos_app():
    assert px_commandline.get_command("/".join([
        "/System",
        "Library",
        "CoreServices",
        "Dock.app",
        "Contents",
        "XPCServices",
        "com.apple.dock.external.extra.xpc",
        "Contents",
        "MacOS",
        "com.apple.dock.external.extra"
    ])) == "Dock/extra"

    # https://github.com/walles/px/issues/73
    assert px_commandline.get_command("/".join([
        "/Applications",
        "Firefox.app",
        "Contents",
        "MacOS",
        "plugin-container.app",
        "Contents",
        "MacOS",
        "plugin-container"
    ])) == "Firefox/plugin-container"

    # Note that if we have spaces inside of the path, the path in
    # question needs to be valid on the local system for it to
    # be deciphered properly by px. So this path is from an actual
    # path, but with all spaces removed.
    assert px_commandline.get_command("/".join([
        "/Applications",
        "VisualStudioCode.app",
        "Contents",
        "Frameworks",
        "CodeHelper(Renderer).app",
        "Contents",
        "MacOS",
        "CodeHelper(Renderer)"
    ])) == "CodeHelper(Renderer)"

    assert px_commandline.get_command("/Applications/iTerm.app/Contents/MacOS/iTerm2") == "iTerm2"

    # Don't duplicate the .app name
    assert px_commandline.get_command("/".join([
        "/System",
        "Library",
        "PrivateFrameworks",
        "IDS.framework",
        "identityservicesd.app",
        "Contents",
        "MacOS",
        "identityservicesd"
    ])) == "IDS/identityservicesd"
