#include <libusb-1.0/libusb.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define GCDC_HID_DATA_IN 0x83
#define TEMPERATURE_REPORT_ID 2
#define PRESSURE_REPORT_ID 4
#define MAX_DEVICES 0x08
#define MAX_SERIAL_NUM 0x80
#define GCDC_HID_INTERFACE 1
#define GCDC_VID 0x10C4
#define GCDC_PID 0x84D1

int mUsbTimeout = 2000;
FILE *mfout = NULL;
char* serialNums[MAX_DEVICES];
char temp[MAX_DEVICES][MAX_SERIAL_NUM];
char refSerialNum[MAX_SERIAL_NUM];
char dutSerialNum[MAX_SERIAL_NUM];
libusb_device_handle* refDevh = NULL; 
libusb_device_handle* dutDevh = NULL; 
libusb_device_handle* devh[MAX_DEVICES]; 
int verbose_flag = 0;
int numDevicesFound = 0;

struct pressureReport
{
    unsigned char reportId;
    u_int16_t timeFsec;
    int16_t timeFmsec;
    int32_t pressure;
};

/* returns a list of serial numbers
   corresponding to 
   devices that this interface can work with
   ctx is the underlying libusb context (NULL for most applicatios)
   list - an array of strings to fill in
   maxEntries - size of the list
   maxSize - max size of each string
   */
int gcdcInterfaceGetSerialNumbers(libusb_context *ctx, char* list[], int maxEntries, int maxSize)
{
    struct libusb_device **devs;
    struct libusb_device *dev;
    libusb_device_handle *handle = NULL;
    int count = 0;
    size_t i = 0;
    int r;
    if (libusb_get_device_list(ctx, &devs) < 0)
        return(0);

    while ((dev = devs[i++]) != NULL) 
    {
        struct libusb_device_descriptor desc;
        r = libusb_get_device_descriptor(dev, &desc);
        if (r < 0)
            goto out;

        if (desc.idVendor == GCDC_VID && desc.idProduct == GCDC_PID) 
        {
            // open device then close it to take a peek at the serial number
            r = libusb_open(dev, &handle);
            if (r < 0)
            {
                handle = NULL;
                continue;
            }
            r = libusb_get_string_descriptor_ascii(handle,desc.iSerialNumber,(unsigned char*)(list[count++]),maxSize);
            libusb_close(handle);
            handle = NULL;
            if( r<0)
            {
                continue;
            }
            if(count >= maxEntries) break;
        }
    }
out:
    libusb_free_device_list(devs, 1);
    return( count);
}

/* 
   Convenience function for finding a device with a particular serial number works 
   when you know the explicit serial number of the device*/
libusb_device_handle* gcdcInterfaceOpenDeviceWithSerialNumber(libusb_context *ctx, char * serialNum)
{
    struct libusb_device **devs;
    struct libusb_device *found = NULL;
    struct libusb_device *dev;
    libusb_device_handle *handle = NULL;
    size_t i = 0;
    int r;
    if (libusb_get_device_list(ctx, &devs) < 0)
        return NULL;

    while ((dev = devs[i++]) != NULL) 
    {
        struct libusb_device_descriptor desc;
        r = libusb_get_device_descriptor(dev, &desc);
        if (r < 0)
            goto out;

        if (desc.idVendor == GCDC_VID && desc.idProduct == GCDC_PID) 
        {
            char buffer[0x80];
            int match;
            // open device then close it to take a peek at the serial number
            r = libusb_open(dev, &handle);
            if (r < 0)
            {
                handle = NULL;
                continue;
            }
            r = libusb_get_string_descriptor_ascii(handle,desc.iSerialNumber,(unsigned char*)(buffer),0x80);
            libusb_close(handle);
            handle = NULL;
            if( r<0)
            {
                continue;
            }

            match = strncasecmp(serialNum,buffer,strlen(serialNum));	
            if(match == 0) 
            {
                found = dev;
                break;
            }
        }
    }

    if (found) 
    {
        r = libusb_open(found, &handle);
        if (r < 0)
            handle = NULL;
    }

out:
    libusb_free_device_list(devs, 1);
    return handle;
}

int usbInterfaceGetRealtimePressure(libusb_device_handle *devh, struct pressureReport* pr)
{
    unsigned char temp[0x40];
    //	if(devh1) devh= devh1;                           
    if(!pr) return(-1);
    while(1)
    {
        int r;
        int xfered;
        r = libusb_interrupt_transfer(devh, GCDC_HID_DATA_IN, temp, 0x40, &xfered, mUsbTimeout);
        if (r < 0) {
            fprintf(stderr, "F0 error %d\n", r);
            return( r) ;
        }

        char reportId = temp[0];
        switch(reportId)
        {
            case PRESSURE_REPORT_ID:
                pr->pressure= le32toh(*(uint32_t*)(temp+5));
                return(0);
                break;
            default:
                break;
        }
    }
    return(-2);
}

int usbInterfaceGetRealtimeTemperature(libusb_device_handle *devh, struct pressureReport* pr)
{
    unsigned char temp[0x40];
    //	if(devh1) devh= devh1;                           
    if(!pr) return(-1);
    while(1)
    {
        int r;
        int xfered;
        r = libusb_interrupt_transfer(devh, GCDC_HID_DATA_IN, temp, 0x40, &xfered, mUsbTimeout);
        if (r < 0) {
            fprintf(stderr, "F0 error %d\n", r);
            return( r) ;
        }

        char reportId = temp[0];
        switch(reportId)
        {
            case TEMPERATURE_REPORT_ID:
                pr->pressure= le32toh(*(uint32_t*)(temp+5));
                return(0);
                break;
            default:
                break;
        }
    }
    return(-2);
}

libusb_device_handle* gcdcInterfaceConnectToSerialNumber(char* serialNumber)
{
    int r=0;
    struct libusb_device_handle* devh = NULL;

    devh = gcdcInterfaceOpenDeviceWithSerialNumber(NULL, serialNumber);
    if (!devh) {
        fprintf(stderr, "Could not find/open <%s>\n",serialNumber);
        goto out;
    }

    r = libusb_kernel_driver_active(devh, GCDC_HID_INTERFACE);
    if (r == 1) {
        r = libusb_detach_kernel_driver(devh, GCDC_HID_INTERFACE);
        if(r<0) {
            printf("libusb_detach_kernel_driver = %d\n", r);
            goto out;
        }
    }
    r = libusb_claim_interface(devh, GCDC_HID_INTERFACE);
    if (r < 0) {
        fprintf(stderr, "ERROR, usb_claim_interface libusb error number: %d\n", r);
        goto out;
    }
    return(devh);

out:
    libusb_close(devh);
    return( NULL);
}


int gcdcInterfaceInit(void)
{
    int r = 1;
    mfout = stderr;        
    r = libusb_init(NULL);
    if (r < 0) {
        fprintf(stderr, "failed to initialise libusb\n");
        return(r);   
    }
    return(r);
}


int init_devices(){

    int i,r;

    for(i=0;i<MAX_DEVICES;i++)
    {
        serialNums[i] = temp[i];
    }

    refSerialNum[0] = '\0';
    dutSerialNum[0] = '\0';

    r = gcdcInterfaceInit();
    if (r < 0) {
        fprintf(stderr, "failed to initialise libusb\n");
        exit(1);
    }

    numDevicesFound = gcdcInterfaceGetSerialNumbers(NULL, serialNums, MAX_DEVICES, MAX_SERIAL_NUM);
    if(numDevicesFound <1)
    {
        printf("Wasn't able to find devices %d\n",numDevicesFound);
        goto out;
    }
    if( numDevicesFound > MAX_DEVICES) numDevicesFound = MAX_DEVICES;

    for(i=0;i< numDevicesFound;i++)
    {
        // open devices
        if(verbose_flag) printf("Connecting to <%s>\n",serialNums[i]);
        devh[i] = gcdcInterfaceConnectToSerialNumber(serialNums[i]);
        if(devh[i] == NULL) goto out;
        if(refSerialNum[0])
        {
            if(strncasecmp(serialNums[i],refSerialNum, MAX_SERIAL_NUM) == 0)
            {
                if(verbose_flag) printf("Reference device found\n");
                refDevh = devh[i];
            }
        }
        if(dutSerialNum[0])
        {
            if(strncasecmp(serialNums[i],dutSerialNum, MAX_SERIAL_NUM) == 0)
            {
                if(verbose_flag) printf("Expected device found\n");
                dutDevh = devh[i];
            }
        }
    }
    return 0;
    out: return 1;
}

double get_pressure(){

    int i;
    struct pressureReport pr[MAX_DEVICES];

    for(i=0;i<numDevicesFound;i++)
    {
        if(usbInterfaceGetRealtimePressure(devh[i], &pr[i]))
            goto out;
    }

    return pr[0].pressure;
out: return 0.0;
}

double get_temperature(){

    int i;
    struct pressureReport pr[MAX_DEVICES];

    for(i=0;i<numDevicesFound;i++)
    {
        if(usbInterfaceGetRealtimeTemperature(devh[i], &pr[i]))
            goto out;
    }

    return pr[0].pressure;
out: return 0.0;
}
