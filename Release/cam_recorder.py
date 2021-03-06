import cv2
import numpy as np
from time import clock
from moviepy.editor import *
import os
import shutil
from pyaudio import PyAudio, paInt16 
from datetime import datetime 
import wave
import multiprocessing as mulp
import serial
import time
import math
import win32api
import win32con

def rec_audio(stat,filename,queue):
	NUM_SAMPLES = 200
	SAMPLING_RATE = 8000
	pa = PyAudio()
	stream = pa.open(format=paInt16, channels=1, rate=SAMPLING_RATE, input=True, frames_per_buffer=NUM_SAMPLES)
	save_count = 0 
	save_buffer = [] 

	while True:
		signal=queue.get()
		if(signal=="audio_start"):
			break

	time_start=clock()

	while True:
		string_audio_data = stream.read(NUM_SAMPLES)
		save_buffer.append( string_audio_data )
		if(stat.value==1):
			break
	
	time_finish=clock()
	wf = wave.open("./temp_frame/"+filename+".wav", 'wb') 
	wf.setnchannels(1) 
	wf.setsampwidth(2) 
	wf.setframerate(SAMPLING_RATE) 
	wf.writeframes("".join(save_buffer)) 
	wf.close() 
	save_buffer = [] 

	print("audio_start: "+str(time_start))
	print("audio_end: "+str(time_finish))
	print("audio_duration (sec): "+str(time_finish-time_start))   #duration (second)
	print ("audio_file: ", filename, "saved" )
	queue.put("wav_sav_ok")

def rec_video(stat,framecnt,filename,queue):
	framelist=[]
	cap=cv2.VideoCapture(2)
	capsize = (int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)),int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)))
	fourcc = cv2.cv.CV_FOURCC('M','S','V','C')
	cv2.namedWindow("test")
	framecnt.value=0
	success, frame = cap.read()
	cv2.imwrite("./temp_frame/0.jpg",frame)
	framelist.append("./temp_frame/0.jpg")
	framecnt.value+=1
	queue.put("rotate_start")
	queue.put("audio_start")
	time_start=clock()

	while True:
		success, frame = cap.read()
		cv2.imwrite("./temp_frame/"+str(framecnt.value)+".jpg",frame)
		framelist.append("./temp_frame/"+str(framecnt.value)+".jpg")
		framecnt.value+=1
		cv2.imshow("test", frame)

		#print(frame.shape)
		#print(type(frame))

		key=cv2.waitKey(10)
		c = chr(key & 255)
		if c in ['q', 'Q', chr(27)]:
			time_finish=clock()
			#with stat.get_lock()
			stat.value = 1
			break

	cap.release()
	cv2.destroyAllWindows()

	while True:
		signal=queue.get()
		if(signal=="wav_sav_ok"):
			print("wav_completed")
			break

	print("video_start: "+str(time_start))
	print("video_end: "+str(time_finish))
	print("video_duration (sec): "+str(time_finish-time_start))   #duration (second)
	print("total frames: "+str(framecnt.value))
	cvfps=framecnt.value/(time_finish-time_start)
	print("fps: "+str(cvfps))                               #fps

	clip=ImageSequenceClip(framelist,fps=cvfps)
	audio_clip=AudioFileClip("./temp_frame/"+filename+".wav")
	sndclip=clip.set_audio(audio_clip)
	sndclip.to_videofile("./"+filename+".mp4",fps=cvfps)

def engine_rotating(stat,framecnt,queue):
	pi=3.14159265358979723846
	ags=[0 for x in range(0,20)]        #angle_sin
	agc=[0 for x in range(0,20)]        #angle_cos
	agh=[0 for x in range(0,20)]
	angle=22.5
	for i in range(1,9):
		agh[i]=2*pi*angle/360
		ags[i]=math.sin(agh[i])
		agc[i]=math.cos(agh[i])
		print(i,angle,agh[i],agc[i])
		angle+=45;

	ser=serial.Serial('COM8',9600)
	ser.write("sssssssss")
	classfier=cv2.CascadeClassifier("D:\\HFUTProject\\cam\\cam_Controller_Py\\haarcascade_frontalface_alt.xml")
	color = (255,0,0)
	while True:
		signal=queue.get()
		if(signal=="rotate_start"):
			break

	print("eng_start")

	while True:
		time.sleep(0.01)			##??
		if(stat.value==1):
			break
		cnt=framecnt.value-1
		frame=cv2.imread("./temp_frame/"+str(cnt)+".jpg")
		size=frame.shape[:2]
		image=np.zeros(size,dtype=np.float16)
		image = cv2.cvtColor(frame, cv2.cv.CV_BGR2GRAY)
		cv2.equalizeHist(image, image)
		divisor=32
		h, w = size
		minSize=(w/divisor, h/divisor)
		faceRects = classfier.detectMultiScale(image, 1.2, 2, cv2.CASCADE_SCALE_IMAGE,minSize)
		#print(cnt,len(faceRects))
		if len(faceRects)>0:
			for faceRect in faceRects:
				x, y, w, h = faceRect
				#print("detected face: ",x,y,w,h)
				#cv2.rectangle(frame, (x, y), (x+w, y+h), color,3)
				cx=x+(w/2)-320
				cy=-(y+(h/2)-240)
				cz=math.sqrt(cx*cx+cy*cy)
				angle_cos=cy/cz
				angle_sin=cx/cz
				#640x480    center:320,240

				if((abs(cx)>100)or(abs(cy)>75)):
					#print(x,x+w,y,y+h,"   ",cx,cy,angle_sin,angle_cos)
					if(angle_sin>0):        #AQWED
						if(angle_cos>agc[1]):           #D
							ser.write("sww")
						elif(angle_cos>agc[2]):      #E
							ser.write("see")
						elif(angle_cos>agc[3]):      #W
							ser.write("sddd")
						elif(angle_cos>agc[4]):      #Q
							ser.write("scc")
						else:                           #A
							ser.write("sxx")
					elif(angle_sin<=0):
						if(angle_cos>agc[8]):           #D
							ser.write("sww")
						elif(angle_cos>agc[7]):      #C
							ser.write("sqq")
						elif(angle_cos>agc[6]):      #X
							ser.write("saaa")
						elif(angle_cos>agc[5]):      #Z
							ser.write("szz")
						else:                           #A
							ser.write("sxx")
					elif((abs(cx)>40)or(abs(cy)>30)):
						#print(x,x+w,y,y+h,"   ",cx,cy,angle_sin,angle_cos)
						if(angle_sin>0):        #AQWED
							if(angle_cos>agc[1]):           #D
								ser.write("sw")
							elif(angle_cos>agc[2]):      #E
								ser.write("se")
							elif(angle_cos>agc[3]):      #W
								ser.write("sdd")
							elif(angle_cos>agc[4]):      #Q
								ser.write("sc")
							else:                           #A
								ser.write("sx")
						elif(angle_sin<=0):
							if(angle_cos>agc[8]):           #D
								ser.write("sw")
							elif(angle_cos>agc[7]):      #C
								ser.write("sq")
							elif(angle_cos>agc[6]):      #X
								ser.write("saa")
							elif(angle_cos>agc[5]):      #Z
								ser.write("sz")
							else:                           #A
								ser.write("sx")

	print("rotating finish")
	cv2.destroyWindow("test")

def gesture(stat):
	print("infraRed_start")
	gcap=cv2.VideoCapture(1)
	cv2.namedWindow("test")
	success,gframe=gcap.read()
	bkg=gframe
	fnt=gframe
	graybkg=cv2.cvtColor(gframe,cv2.COLOR_BGR2GRAY)
	grayfnt=cv2.cvtColor(gframe,cv2.COLOR_BGR2GRAY)
	vec=[0 for x in range(0,10)]
	veccnt=0

	mova=-1
	movb=-1
	clear_mov=0
	while success:
		time.sleep(0.01)
		if(stat.value==1):
			break
		success,gframe=gcap.read()
		rad=5		#radius of Gaussian blur must be odd
		grayframe=cv2.cvtColor(gframe,cv2.COLOR_BGR2GRAY)
		grayframe=cv2.GaussianBlur(grayframe, (rad,rad), 0)
		#grayfnt=cv2.absdiff(grayframe,graybkg)
		#grayfnt=grayframe-graybkg
		bkg=gframe
		graybkg=cv2.cvtColor(gframe,cv2.COLOR_BGR2GRAY)
		(minval,maxval,minloc,maxloc)=cv2.minMaxLoc(grayframe)
		if(maxval>150):
			cv2.circle(gframe,maxloc,rad,(255,0,0),2)
			cv2.circle(grayframe,maxloc,rad,(255,0,0),2)

			vec[veccnt]=maxloc[0]
			#print(vec[veccnt])
			veccnt+=1
			#moved=1

			if(veccnt==10):
				clear_mov=1-clear_mov
				if(clear_mov==1):
					mova=-1
					movb=-1
					print("clear!")

				veccnt=0
				avr=0
				for i in range(1,10):
					speed=abs(vec[i]-vec[i-1])
					avr+=speed
					print(i,speed)
				avr=avr/10
				if(avr>6):
					if(vec[9]>vec[0]):
						if(mova==-1):
							mova=1
						else:
							movb=1
						print("right",mova,movb)
						#win32api.keybd_event(34,0,0,0)
						#win32api.keybd_event(34,0,win32con.KEYEVENTF_KEYUP,0)
					else:
						if(mova==-1):
							mova=0
						else:
							movb=0
						print("left",mova,movb)
						#win32api.keybd_event(33,0,0,0)
						#win32api.keybd_event(33,0,win32con.KEYEVENTF_KEYUP,0)

				if((mova!=-1)and(movb!=-1)):
					if((mova==1)and(movb==0)):
						print("rl")
						win32api.keybd_event(34,0,0,0)		##PAGE_DOWN
						win32api.keybd_event(34,0,win32con.KEYEVENTF_KEYUP,0)
					elif((mova==0)and(movb==1)):
						print("lr")
						win32api.keybd_event(33,0,0,0)		##PAGE_UP
						win32api.keybd_event(33,0,win32con.KEYEVENTF_KEYUP,0)
		cv2.imshow("test",gframe)

		key=cv2.waitKey(1)
		c = chr(key & 255)
		#if c in ['q', 'Q', chr(27)]:
		#	break

	cv2.destroyWindow("test")





if __name__=='__main__':
	recording_status=mulp.Value('i',0)
	recording_cnt=mulp.Value('i',0)
	filename = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")

	queue = mulp.Queue(4)
	p1=mulp.Process(target=rec_audio,args=(recording_status,filename,queue,))
	p2=mulp.Process(target=rec_video,args=(recording_status,recording_cnt,filename,queue,))
	p3=mulp.Process(target=engine_rotating,args=(recording_status,recording_cnt,queue,))
	p4=mulp.Process(target=gesture,args=(recording_status,))
	p1.start()
	p2.start()
	p3.start()
	p4.start()
	p1.join()
	p2.join()
	p3.join()
	p4.join()
	queue.close()


