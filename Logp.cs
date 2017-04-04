using System;
using System.IO;
using System.Configuration;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;

namespace Logp
{
    /// <summary>
    /// An entry of the final result.
    /// A tuple of filename, line number and the line itself.
    /// </summary>
    public class LineTuple
    {
        public LineTuple(string fileName, int lineNumber, string line)
        {
            this.FileName = fileName;
            this.LineNumber = lineNumber;
            this.Line = line;
        }
        public string FileName;
        public int LineNumber;
        public string Line;
    }


    /// <summary>
    /// A tuple of filename and the file stream object.
    /// </summary>
    public class FileTuple
    {
        public FileTuple(string fileName, StreamReader file)
        {
            this.FileName = fileName;
            this.File = file;
        }
        public string FileName;
        public StreamReader File;
    }


    /// <summary>
    /// A generator-style find function.  Given a file pattern,
    /// and a list of paths, find all paths that match the pattern
    /// and yield each path.
    /// </summary>
    public class GFind
    {
        public GFind(string filePattern, IEnumerable<string> rootPaths, OnErrorDelegate d)
        {
            _filePattern = filePattern;
            _rootPaths = rootPaths;
            _d = d;
        }

        public delegate void OnErrorDelegate(Exception e);

        public IEnumerable<string> Run()
        {
            foreach (string rootPath in _rootPaths)
            {
                string[] paths;
                try
                {
                    paths = Directory.GetFiles(rootPath, _filePattern, 
                        SearchOption.AllDirectories);
                }
                catch (Exception e)
                {
                    _d(e);
                    continue;
                }
                foreach (string path in paths)
                {
                    yield return path;
                }
            }
        }

        private IEnumerable<string> _rootPaths;
        private string _filePattern;
        private OnErrorDelegate _d;
    }

    
    /// <summary>
    /// A generator-style open function.  Given a list of
    /// paths, open and yield each path.
    /// </summary>
    public class GOpen
    {
        public GOpen(IEnumerable<string> paths)
        {
            _paths = paths;
        }

        public IEnumerable<FileTuple> Run()
        {
            foreach (string path in _paths)
            {
                yield return new FileTuple(path, new StreamReader(path));
            }
        }

        private IEnumerable<string> _paths;
    }


    /// <summary>
    /// A generator-style cat (concatenation) function.  Given
    /// a list of file tuples, yield each line in the file as a
    /// LineTuple object.
    /// </summary>
    public class GCat
    {
        public GCat(IEnumerable<FileTuple> fileTuples)
        {
            _fileTuples = fileTuples;
        }

        public IEnumerable<LineTuple> Run()
        {
            foreach (FileTuple fileTuple in _fileTuples)
            {
                int lineNum = 0;
                StreamReader f = fileTuple.File;
                while (true)
                {
                    string line = f.ReadLine();
                    if (line == null) break;
                    lineNum++;
                    yield return new LineTuple(fileTuple.FileName, lineNum, line);
                }
            }
        }

        private IEnumerable<FileTuple> _fileTuples;
    }


    /// <summary>
    /// A generator-style grep function.  Given a grep pattern
    /// and a list of LineTuple, see if each line match the
    /// grep pattern.  If it matches, yield that LineTuple.
    /// </summary>
    public class GGrep
    {
        public GGrep(string pattern, IEnumerable<LineTuple> lines)
        {
            _re = new Regex(pattern, RegexOptions.Compiled);
            _lines = lines;
        }

        public IEnumerable<LineTuple> Run()
        {
            foreach (LineTuple line in _lines)
            {
                if (_re.IsMatch(line.Line))
                {
                    yield return line;
                }
            }
        }

        private Regex _re;
        private IEnumerable<LineTuple> _lines;
    }


    /// <summary>
    /// This class just handles the outputting to the console and
    /// hooking up all the G-classes.  Consider this the console 
    /// application, while the previous class are reusable libraries.
    /// </summary>
    public static class Logp
    {
        public static void PrintError(Exception e)
        {
            Console.WriteLine("[{0}] {1}", DateTime.Now, e);
        }

        public static void Grep(IEnumerable<string> servers, 
            string rootDir, string filePattern, string pattern)
        {
            Console.WriteLine(
                "Finding pattern <{0}> in files <{1}> from folders (and their subfolders):", 
                pattern, filePattern);
            
            List<string> rootPaths = new List<string>(servers.Count<string>());
            for (int i = 0; i < servers.Count<string>(); i++)
            {
                rootPaths.Add(Path.Combine(@"\\" + servers.ElementAt<string>(i), rootDir));
                Console.WriteLine(rootPaths[i]);
            }

            Console.WriteLine("[{0}] Start searching...", DateTime.Now);
            GFind gfind = new GFind(filePattern, rootPaths, new GFind.OnErrorDelegate(PrintError));
            GOpen gopen = new GOpen(gfind.Run());
            GCat gcat = new GCat(gopen.Run());
            GGrep ggrep = new GGrep(pattern, gcat.Run());

            int count = 0;
            foreach (LineTuple result in ggrep.Run())
            {
                count++;
                Console.WriteLine("[{0}] {1}|{2}|{3}", 
                    DateTime.Now, result.FileName, result.LineNumber, result.Line);
            }

            Console.WriteLine("[{0}] {1} entries found.  Finished.", DateTime.Now, count);
        }

        public static void Main(string[] args)
        {
            List<string> servers = new List<string>();
            NameValueCollection appSettings = ConfigurationManager.AppSettings;

            string[] serverGroups = appSettings["Servers"].Split(',');
            foreach (string group in serverGroups)
            {
                string val = appSettings["Servers." + group];
                if (val != null)
                {
                    servers.AddRange(val.Split(','));
                }
            }

            string rootDir = appSettings["RootDirectory"];
            string filePattern = appSettings["FilePattern"];
            string pattern = appSettings["Pattern"];

            Logp.Grep(servers, rootDir, filePattern, pattern);
        }
    }

}
