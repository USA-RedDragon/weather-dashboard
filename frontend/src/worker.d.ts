type Message = {
    type: string;
    payload: any;
};

type azimuthRangeToLatLonOptions = {
    azimuths: number[];
    ranges: number[];
    center_lat: number;
    center_lon: number;
    data: number[][];
};

type azimuthRangeToLatLonResult = {
    xlocs: number[][];
    ylocs: number[][];
    data: number[][];
};
