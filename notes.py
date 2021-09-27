import squirrel
import configparser
import toolbelt
quickdate = toolbelt.quickdate.quickdate


# Note interpreter
class NoteInterpreter(squirrel.squish.SquishInterpreter):

    def __init__(self):
        self.objects = ['note', 'todo', 'reminder'];
        if not self.commands:
           self.commands = {};
        self.commands.update({
           'quicknote' : { 
             'func' : self.quicknote, 
             'args' :  {'quicknote': ''},
             'opts' : {
                'log'  : 'Create a quick todo note',
                'help' : 'quicknote color category subject remind, quicknote',
                'fail' : 'Failed to describe object',
             }
           },
        });
        super().__init__();
        self.initialize_squids();
        self.initialize_autocomplete();
        super().initialize_autocomplete();


    def initialize_autocomplete(self):
        import re;
        self.ts = {
          'note'     : ['category', 'subject', 'color'],
          'todo'     : ['category', 'subject', 'color'],
          'reminder' : ['who', 'about', 'what', 'time', 'how'],
        }
        quicknote = "(?P<color>\w+) (?P<category>\w+) (?P<subject>\w+) (?P<remind>(\w+| )+), (?P<quicknote>.*)"
        self.argspec = [{
              'key'      : 'quicknote',
              'pattern'  : re.compile(quicknote), 
              'optional' : True,
        }];


    def initialize_squids(self):
        notebook = Notebook();
        self.squids = notebook.squids;


    # Interesting bug... 'note' in quicknote sets 'obj', which triggers
    # note squid to load
    def quicknote(self, args):
        self.squid = self.squids['todo'];
        string = args['quicknote'] 
        df     = args['argspec']
        p = df[df['key']=='quicknote']['pattern'].iloc[0]
        m = p.match(string);
        args['dates'] = True;
        args = self.load_form(args, self.squids['todo'].form['new']);
        args = self.load_presets(args, self.squids['todo'].form['new']);
        data = m.groupdict();
        for k in data: args['data'][k] = data[k];
        self.squids['todo'].insert(args['data']);
        return self.preprocess({
         'data' : {
          'cmd': 'view',
          'obj': 'todo',
          'sql': 'id=%s' % self.squids['todo'].getmaxid(),
          'xs' : '',
          }
        });


    def help(self):
        self.log.info("syntax: [command] ...\n");
        super().help();
        objects = [
          'note'
        ]
        self.log.outfile.write("\n");
        self.log.info("objects:");
        for obj in objects:
            self.log.info("  "+obj);
        self.log.outfile.write("\n");




class NotebookSquid(squirrel.squid.Squid):
      def __init__(self):
          super().__init__();
          configs = {};
          configs = configparser.ConfigParser()
          configs.read(
              '/home/dominic/.config/notebook/notebook.cfg'
          )
          self.config = configs['main'];




class NoteSquid(NotebookSquid):
      def __init__(self): 
          super().__init__();
          self.table = "notes";
          self.alias = 'note';
          self.form  = {
            'search' : {
              'defaults' : ['category', 'color', 'subject', 'id'],
            },
            'new'  : { 'fields' : ['id',  'modified',  'category', 'color', 'subject', 'note'], },
            'edit' : { 'fields' : ['id',  'modified',  'category', 'color', 'subject', 'note'], },
            'list' : { 
                'fields' : ['id',  'modified',  'category', 'color', 'subject', 'note'], 
                'order'  : 'order by color',
            },
            'view' : { 'fields' : ['id',  'modified',  'category', 'color', 'subject', 'note'], },
            'join'  : [],
          };



class ToDoSquid(NotebookSquid):
      def __init__(self):
          super().__init__();
          self.alias = 'todo';
          self.table = "todos";
          self.form = {
            'search' : { 
              'defaults' : ['id', 'color', 'category', 'subject', 'author'],
              'order'  : 'order by color desc',
              },
            'new': { 'fields':   ['color', 'category', 'subject', 'remind', 'quicknote'],
                     'preset': {
                       'color'    : 'red',
                       'category' : 'todo',
                       'created'  : 'now',
                       'modified' : 'now',
                       'deadline' : 'now',
                       'finished' : 'now',
                       'priority' :  3,
                     }
                   },
            'edit' : { 'fields':   ['color', 'category', 'subject', 'remind', 'quicknote'],
                       'preset': {
                         'modified' : 'now',
                       }
            },
            'view':{'fields': ['id',       'priority', 'category', 'subject',  
                               'deadline', 'remind',   'tags',       'note']
            },
            'list':{'fields': ['id',       'color',    'priority', 'deadline', 'remind',   
                               'category', 'subject',  'quicknote'],
                'order'  : 'order by color',
            },
            'join'  : [
            ],
          };


class ReminderSquid(NotebookSquid):


      def postprocessor(self, args):
          self.update({
               'id'    : args['data']['id'],
               'often' : 'time' if args['data']['often'] != 'once' else 'once',
               'next'  : quickdate(args['data']['time']),
          });
          return args;


      def __init__(self): 
          super().__init__();
          self.table = "reminder";
          self.form  = {
            'search' : {
              'defaults' : ['id', 'who', 'about', 'how', 'often', 'time', 'what'],
            },
            'new'   : { 
               'fields' : ['who',  'about', 'how', 'often', 'time', 'what'], 
               'postprocessor': self.postprocessor,
            },
            'edit'  : { 'fields' : ['id',  'who',  'about', 'how', 'often', 'time', 'what'], 
               'postprocessor': self.postprocessor,
            },
            'list'  : { 'fields' : ['id',  'who',  'about', 'how', 'often', 'time', 'next', 'what'], },
            'view'  : { 'fields' : ['id',  'who',  'about', 'how', 'often', 'time', 'next', 'what'], },
            'join'  : [],
          };


class Note(squirrel.squish.Squish, NoteSquid):
      def __init__(self):
          NoteSquid.__init__(self);

class ToDo(squirrel.squish.Squish, ToDoSquid):
      def __init__(self):
          ToDoSquid.__init__(self);

class Reminder(squirrel.squish.Squish, ReminderSquid):
      def __init__(self):
          ReminderSquid.__init__(self);


class Notebook():

      def __init__(self):
          self.aliases = {
             'todos'    : 'todo',
             'notes'    : 'note',
          }
          self.note     = Note();
          self.todo     = ToDo();
          self.reminder = Reminder();
          self.squids={}
          self.squids['note']     = self.note;
          self.squids['todo']     = self.todo;
          self.squids['reminder'] = self.reminder;
          for squid in self.squids:
              self.squids[squid].db = self;

      def squids(self):
          return self.squids;
