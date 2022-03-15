import numpy as np
import csv
import matplotlib.pyplot as plt

def import_csv (path, verbose=True):
    # this will read the header 
    ifile  = open(path, "r")
    read = csv.reader(ifile)
    for row in read :
        header = row
        break

    #this will read the numbers
    array = np.genfromtxt(path, delimiter=',')[1:,:] #the last thing removes the first row which is the header

    if verbose == True: 
        print ('header')
        print (header)
        print ('')
        print ('shape of imported array')
        print (array.shape)

        plt.plot (array[:,0])
        plt.title('sequence')
        plt.xlabel('location in array')
        plt.ylabel('sequence')
        plt.show()

        plt.plot (array[:,1])
        plt.title('battery')
        plt.xlabel('sample number')
        plt.ylabel('battery level')
        plt.show()

        plt.plot (array[:,2])
        plt.title('flags')
        plt.xlabel('sample number')
        plt.ylabel('raised flags')
        plt.show()

        plt.plot (array[0:100,3])
        plt.title('first channel')
        plt.xlabel('sample number (extrat)')
        plt.ylabel('value')
        plt.show()

    return (header, array)


def find_start_row (ref, test):
    number_of_similarities=0
    for i in range (len (ref)):    
        test_initial_row = np.round (test [0,:])
        ref_row = np.round (ref[i,3:])
        similarity = np.sum(np.all(test_initial_row == ref_row, axis=0))
        #similarity_indx = np.sum(test_initial_row == ref_row, axis=0) 
        #if similarity_indx > 29:
        if similarity > 0: 
            print ('frame {} of ref matches the first frame of test'.format (i))
            start_row = i
            number_of_similarities+=1
    
    print (number_of_similarities)

    if number_of_similarities == 1:
        return (start_row)
    else: 
        print ('ATTENTION: no start row could be defined becuase there are too many or too little alignments')


def find_gaps (ref, test, start_row):
    n_gaps = 0
    gaps = []
    recent_drops = np.zeros(100)
    gaps_percentage = []
    drops_in_a_row = 0

    for i in range (len (test)):
        test_row = np.round (test [i,:])
        ref_row = np.round (ref[start_row+i+n_gaps,3:])
        similarity_indx = np.sum((test_row == ref_row))
        if similarity_indx < 25:             
            recent_drops = np.append(recent_drops[1:],1)
            n_gaps +=1
            gaps.append(i)
            gaps_percentage.append(np.mean(recent_drops))
            drops_in_a_row += 1
        else: 
            if drops_in_a_row != 0:
                #print ('there were {} drops in a row'.format(drops_in_a_row))
                drops_in_a_row = 0
            recent_drops = np.append(recent_drops[1:],0)
            gaps_percentage.append(np.mean(recent_drops))
    #print (gaps)
    return (gaps, gaps_percentage)


def print_gaps (ref,test, start_row, gaps, gaps_percentage = None):
    gaps_array=np.asarray(gaps)
    gaps_plotting = np.zeros(len(ref))

    for i in range(len(gaps_array)):
        gaps_plotting[start_row+gaps_array[i]]=1

    fig, ax = plt.subplots()
    ax.plot(gaps_plotting, color='black')
    #ax.plot(gaps_percentage, color='black')
    #ax.plot(gaps_array, np.ones(len(gaps_array)), 'ro')
    ax.axvspan(0, start_row, alpha=0.5, color='red')
    ax.axvspan(start_row+len(test),len(ref), alpha=0.5, color='red')
    ax.set_title('data loss during Bluetooth transmission')
    ax.set_xlabel('samples of the SD recording')
    ax.set_ylabel('data transmission (red=not recorded, 1=lost)')
    # ax.set_xlim(left=start_row-1000) #to zoom in 
    plt.show()


def analyse_gaps (ref,test):
    start_row = find_start_row(ref, test)
    gaps, gaps_percentage = find_gaps(ref, test, start_row)
    print_gaps(ref, test, start_row, gaps, gaps_percentage)
