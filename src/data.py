from dataclasses import dataclass, field, asdict
from builder import RequestBuilder
import pandas as pd
import re

LIST_SEP = ","

# traffic column constant
BUKKEN_TRAFFIC_SEP = "<br>"
BUKKEN_STATION_SEP_PATTERN = r'、|または'
BUKKEN_STATION_BUILDING_NUM_PATTERN = r'(（.*）)'
BUKKEN_TRAFFIC_REGEX_STATION_GROUP = "station"
BUKKEN_TRAFFIC_REGEX_BUS_GROUP = "bus"
BUKKEN_TRAFFIC_REGEX_WALK_GROUP = "walk"
# ^(?<station>[^バス|徒歩]+)?[ ]?(バス(?<bus>[0-9～]+)分)?[ ]?(徒歩(?<walk>[0-9～]+)分)?[ ]?$
BUKKEN_TRAFFIC_REGEX = f"^(?P<{BUKKEN_TRAFFIC_REGEX_STATION_GROUP}>[^バス|徒歩| ]+)?[ ]?(バス(?P<{BUKKEN_TRAFFIC_REGEX_BUS_GROUP}>[0-9～]+)分)?[ ]?(徒歩(?P<{BUKKEN_TRAFFIC_REGEX_WALK_GROUP}>[0-9～]+)分)?[ ]?$"
BUKKEN_TRAFFIC_MINUTE_REGEX_FROM_GROUP = "from"
BUKKEN_TRAFFIC_MINUTE_REGEX_TO_GROUP = "to"
BUKKEN_TRAFFIC_MINUTE_REGEX = f"(?P<{BUKKEN_TRAFFIC_MINUTE_REGEX_FROM_GROUP}>[0-9]+)(～)?(?P<{BUKKEN_TRAFFIC_MINUTE_REGEX_TO_GROUP}>([0-9]+))?"

# room column constant
ROOM_FLOOR_COLUMN_NAME = "floor"
ROOM_FLOOR_SPACE_COLUMN_NAME = "floorSpace"
ROOM_RENT_COLUMN_NAME = "rent"
ROOM_TOTAL_COLUMN_NAME = "total"
ROOM_SHIKIKIN_COLUMN_NAME = "shikikin"
ROOM_TRAFFIC_COLUMN_NAME = "traffic"
ROOM_COMMON_FEE_COLUMN_NAME = "commonFee"
ROOM_SYSTEMS_COLUMN_NAME = "systems"

# station column constant
STATIONS_COLUMN_NAME = "stations"
STATION_BY_WALK_COLUMN_NAME = "byWalk"
STATION_NEAREST_STATION_BY_WALK_COLUMN_NAME = f"{STATION_BY_WALK_COLUMN_NAME}.nearestStation"
STATION_BEST_CASE_BY_WALK_COLUMN_NAME = f"{STATION_BY_WALK_COLUMN_NAME}.bestCaseMinute"
STATION_WORST_CASE_BY_WALK_COLUMN_NAME = f"{STATION_BY_WALK_COLUMN_NAME}.worstCaseMinute"
STATION_BY_BUS_COLUMN_NAME = "byBus"
STATION_NEAREST_STATION_BY_BUS_COLUMN_NAME = f"{STATION_BY_BUS_COLUMN_NAME}.nearestStation"
STATION_BEST_CASE_BY_BUS_COLUMN_NAME = f"{STATION_BY_BUS_COLUMN_NAME}.bestCaseMinute"
STATION_WORST_CASE_BY_BUS_COLUMN_NAME = f"{STATION_BY_BUS_COLUMN_NAME}.worstCaseMinute"

# bukken fields mappings
BUKKEN_RECORD_PATH = "rooms"
BUKKEN_CITY_COLUMN_NAME = "city"
BUKKEN_AREA_COLUMN_NAME = "area"
BUKKEN_DAN_CHI_COLUMN_NAME = "danChiName"
BUKKEN_ADDRESS_COLUMN_NAME = "address"
BUKKEN_META = [
    BUKKEN_CITY_COLUMN_NAME,
    BUKKEN_AREA_COLUMN_NAME,
    BUKKEN_DAN_CHI_COLUMN_NAME,
    ROOM_TRAFFIC_COLUMN_NAME,
    BUKKEN_ADDRESS_COLUMN_NAME,
]
BUKKEN_FIELDS = {
    "Todofuken": BUKKEN_CITY_COLUMN_NAME,
    "Area": BUKKEN_AREA_COLUMN_NAME,
    "Dan Chi Name": BUKKEN_DAN_CHI_COLUMN_NAME,
    "Total Fee": ROOM_TOTAL_COLUMN_NAME,
    "Nearest station by Walk": STATION_NEAREST_STATION_BY_WALK_COLUMN_NAME,
    "Best case by Walk (minute)": STATION_BEST_CASE_BY_WALK_COLUMN_NAME,
    "Worst case by Walk (minute)": STATION_WORST_CASE_BY_WALK_COLUMN_NAME,
    "Nearest station by Bus": STATION_NEAREST_STATION_BY_BUS_COLUMN_NAME,
    "Best case by Bus (minute)": STATION_BEST_CASE_BY_BUS_COLUMN_NAME,
    "Worst case by Bus (minute)": STATION_WORST_CASE_BY_BUS_COLUMN_NAME,
    "Address": BUKKEN_ADDRESS_COLUMN_NAME,
    "Building Name": "buildingName",
    "Floor": ROOM_FLOOR_COLUMN_NAME,
    "Room Num": "roomNum",
    "Room Type": "roomType",
    "Floor Space": ROOM_FLOOR_SPACE_COLUMN_NAME,
    "Max Floor": "maxFloor",
    "Rent": ROOM_RENT_COLUMN_NAME,
    "Common Fee": ROOM_COMMON_FEE_COLUMN_NAME,
    "Shikikin": ROOM_SHIKIKIN_COLUMN_NAME,
    "Systems": ROOM_SYSTEMS_COLUMN_NAME,
    "availableDate": "availableDate",
    "Room Link": "link",
    "Traffic": ROOM_TRAFFIC_COLUMN_NAME,
}


@dataclass
class StationDetail:
    def __init__(self, nearestStation=None, bestCaseMinute=None, worstCaseMinute=None):
        self.nearestStation = nearestStation
        self.bestCaseMinute = bestCaseMinute
        self.worstCaseMinute = worstCaseMinute

    # nearest station
    nearestStation: str
    # best case Minute
    bestCaseMinute: int
    # worst case minute
    worstCaseMinute: int


@dataclass
class Station:
    def __init__(self, byWalk=None, byBus=None):
        self.byWalk = StationDetail() if byWalk is None else byWalk
        self.byBus = StationDetail() if byBus is None else byBus

    # by walk
    byWalk: StationDetail
    # by bus
    byBus: StationDetail


@dataclass
class Room:
    # building name
    buildingName: str = ""
    # room
    roomNum: str = ""
    # room type
    roomType: str = ""
    # floor space
    floorSpace: float = 0
    # floor
    floor: int = 0
    # stations json string
    stations: list[Station] = field(default_factory=list)
    # top floor of building
    maxFloor: int = 0
    # rent
    rent: int = 0
    # common fee
    commonFee: int = 0
    # total fee, rent + common fee
    total: int = 0
    # shikikin required
    shikikin: str = None
    # system
    systems: list = field(default_factory=list)
    # link of room
    link: str = None
    availableDate: str = ""


@dataclass
class Bukken:
    # todofuken
    city: str = ""
    # area of city
    area: str = ""
    # dan chi name
    danChiName: str = ""
    # traffic of raw response
    traffic: str = ""
    # address of building
    address: str = ""
    # list of rooms
    rooms: list[Room] = field(default_factory=list)


class Converter:
    def __init__(self, isDev=False):
        self.requestBuilder = RequestBuilder(isDev)

    # to int
    def toInt(self, x):
        return int("".join(c for c in x if c.isdigit()))

    # convert to room
    def toRoom(self, json):
        room = Room(
            buildingName=json["roomNmMain"],
            roomNum=json["roomNmSub"],
            roomType=json["type"],
            floorSpace=json["floorspace"],
            floor=json["floor"],
            rent=json["rent"],
            commonFee=json["commonfee"],
            shikikin=json["shikikin"],
            systems=json["system"],
            link=f"https://www.ur-net.go.jp{json['roomLinkPc']}",
        )
        return self.decorateDetail(room, json)

    def decorateDetail(self, room, json):
        try:
            response = self.requestBuilder.postRoomDetails(id=json["id"], shisya=json["shisya"], danchi=json["danchi"], shikibetu=json["shikibetu"])[0]
            room.maxFloor = self.toInt(response["floor_sp"][4:])
            room.availableDate = response["availableDate"]
            room.shikikin = response["shikikin"]
        except Exception as e:
            print(f"[error] unable to decorate detail, {e}")

        return room

    # common to station detail function for to station method
    def toStationDetailForStation(self, trafficMatch, group: str, nearestStation: str, bestCaseMinute: int, worstCaseMinute: int, stationDetail: StationDetail):
        groupMatch = trafficMatch.group(group)
        if groupMatch is None:
            return stationDetail

        minuteMatch = re.search(BUKKEN_TRAFFIC_MINUTE_REGEX, groupMatch)
        bestCaseMatch = minuteMatch.group(BUKKEN_TRAFFIC_MINUTE_REGEX_FROM_GROUP)
        worstCaseMatch = minuteMatch.group(BUKKEN_TRAFFIC_MINUTE_REGEX_TO_GROUP)
        bestCaseMinute += int(bestCaseMatch)
        worstCaseMinute += int(worstCaseMatch) if worstCaseMatch is not None else int(bestCaseMatch)

        # assign to station
        if stationDetail.nearestStation is None:
            return StationDetail(nearestStation, bestCaseMinute, worstCaseMinute)
        else:
            return StationDetail(nearestStation, min(stationDetail.bestCaseMinute, bestCaseMinute), max(stationDetail.worstCaseMinute, worstCaseMinute))

    # convert traffic to station details
    def toStation(self, str: str):
        station = Station()

        traffics = re.split(BUKKEN_STATION_SEP_PATTERN, str)

        # to store the first station group
        nearestStation = None

        for traffic in traffics:

            trafficMatch = re.search(BUKKEN_TRAFFIC_REGEX, traffic)

            if (trafficMatch is None):
                print("[error] unable to process traffic", traffic)
                return station

            stationGroup = trafficMatch.group(BUKKEN_TRAFFIC_REGEX_STATION_GROUP)
            nearestStation = re.sub(BUKKEN_STATION_BUILDING_NUM_PATTERN, "", stationGroup) if nearestStation is None else nearestStation

            # bus
            busGroup = trafficMatch.group(BUKKEN_TRAFFIC_REGEX_BUS_GROUP)
            if busGroup is not None:
                busMatch = re.search(BUKKEN_TRAFFIC_MINUTE_REGEX, busGroup)
                bestCaseByBusMatch = busMatch.group(BUKKEN_TRAFFIC_MINUTE_REGEX_FROM_GROUP)
                worstCaseByBusMatch = busMatch.group(BUKKEN_TRAFFIC_MINUTE_REGEX_TO_GROUP)
                bestCaseMinute = int(bestCaseByBusMatch)
                worstCaseMinute = int(worstCaseByBusMatch) if worstCaseByBusMatch is not None else int(bestCaseByBusMatch)
                # bus + walk
                station.byBus = self.toStationDetailForStation(trafficMatch, BUKKEN_TRAFFIC_REGEX_WALK_GROUP, nearestStation, bestCaseMinute, worstCaseMinute, station.byBus)
            else:
                # walk
                station.byWalk = self.toStationDetailForStation(trafficMatch, BUKKEN_TRAFFIC_REGEX_WALK_GROUP, nearestStation, 0, 0, station.byWalk)

        return station

    # compare station detail and return the best & wrose minutes case for to station list method
    def toStationDetailForStationsList(self, currentDetail: StationDetail, nextDetail: StationDetail):
        if currentDetail.nearestStation is None:
            return nextDetail
        elif nextDetail.nearestStation is not None:
            return StationDetail(nextDetail.nearestStation, min(currentDetail.bestCaseMinute, nextDetail.bestCaseMinute), max(currentDetail.worstCaseMinute, nextDetail.worstCaseMinute))
        return currentDetail

    # convert traffic to station details
    def toStations(self, str: str):
        stations: dict[Station] = {}
        for traffic in str.split(BUKKEN_TRAFFIC_SEP):
            station: Station = self.toStation(traffic)
            key = station.byWalk.nearestStation if station.byWalk.nearestStation is not None else station.byBus.nearestStation
            if key not in stations:
                stations[key] = station
            else:
                currentStation = stations[key]
                currentStation.byWalk = self.toStationDetailForStationsList(currentStation.byWalk, station.byWalk)
                currentStation.byBus = self.toStationDetailForStationsList(currentStation.byBus, station.byBus)

        return list(stations.values())

    # convert to bukken
    def toBukken(self, json):
        # init base information of Bukken
        bukken = Bukken(
            city=json["tdfk"],
            area=json["shopHtmlName"],
            danChiName=json["danchiNm"],
            traffic=json["traffic"],
            address=json["place"],
        )

        # convert traffic
        stations = self.toStations(json[ROOM_TRAFFIC_COLUMN_NAME])

        # convert room
        for roomJson in json.get("room", []):
            room: Room = self.toRoom(roomJson)
            room.stations = stations
            bukken.rooms.append(room)
        return bukken

    # convert to data frame
    def toDf(self, bukken):
        df = pd.json_normalize(data=asdict(bukken), record_path=BUKKEN_RECORD_PATH, meta=BUKKEN_META)

        if df.empty:
            return df

        # floor to int, e.g. 5階 -> 5
        df[ROOM_FLOOR_COLUMN_NAME] = df[ROOM_FLOOR_COLUMN_NAME].apply(lambda x: pd.Series(int(x[:len(x) - 1])))

        # rent to int
        df[ROOM_RENT_COLUMN_NAME] = df[ROOM_RENT_COLUMN_NAME].apply(lambda x: pd.Series(self.toInt(x)))

        # common fee to int
        df[ROOM_COMMON_FEE_COLUMN_NAME] = df[ROOM_COMMON_FEE_COLUMN_NAME].apply(lambda x: pd.Series(self.toInt(x)))

        # total = rent + common fee
        df[ROOM_TOTAL_COLUMN_NAME] = df[ROOM_RENT_COLUMN_NAME] + df[ROOM_COMMON_FEE_COLUMN_NAME]

        # floor space to int, e.g. 48&#13217 -> 48
        df[ROOM_FLOOR_SPACE_COLUMN_NAME] = df[ROOM_FLOOR_SPACE_COLUMN_NAME].apply(lambda x: pd.Series(int(x.replace("&#13217;", ""))))

        # system name to list, e.g. [{'制度_IMG': 'btn_u35.png', '制度名': 'U35割', '制度HTML': 'u35'}] -> ["U35割"]
        df[ROOM_SYSTEMS_COLUMN_NAME] = df[ROOM_SYSTEMS_COLUMN_NAME].apply(lambda systems: pd.Series(str(list(map(lambda x: x["制度名"], systems)))))

        # station json array to different rows & columns
        df = df.explode(STATIONS_COLUMN_NAME).reset_index(drop=True)
        df = df.merge(pd.json_normalize(df[STATIONS_COLUMN_NAME]), left_index=True, right_index=True).drop(STATIONS_COLUMN_NAME, axis=1)

        return df
