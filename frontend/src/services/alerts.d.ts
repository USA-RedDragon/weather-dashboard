type WXAlert = {
    instruction: string;
    max_hail_size: number | null;
    max_wind_speed: number | null;
    message_type: string;
    onset: Date;
    sent: Date;
    severity: string;
    state: string;
    urgency: string;
    id: string;
    headline: string;
    geometry: any;
    expires: Date;
    event: string;
    ends: Date;
    effective: Date;
    description: string;
    color: string;
    certainty: string;
    area_desc: string;
    is_weather: boolean;
}
