export function organizeData(data:any ) {
  console.log("Organizing data", data);
  if (Object.keys(data).length === 0) {
    return {};
  }
  // create a dictionary, where the key is the device type and the value is a list of dictionaries of the devices
  const organizedData = data.reduce((acc:any , device:any ) => {
    if (!acc[device.type]) {
      acc[device.type] = [];
    }
    acc[device.type].push(device);
    return acc;
  }, {});
  return organizedData;
}
