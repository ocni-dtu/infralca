import importlib.metadata
import json
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Self

from lcax import (
    EPD,
    Standard,
    Unit,
    Country,
    SubType,
    Source,
    LifeCycleStage,
    ImpactCategoryKey,
    Product, ImpactDataSource1, Transport
)


class LCAxStandard:
    @classmethod
    def from_data_type(cls, data: str) -> Standard:
        if data is None:
            return Standard.UNKNOWN
        elif data == "R":
            return Standard.EN15804A2
        elif data == "R13":
            return Standard.EN15804A1
        elif data in ["R,R13", "R, R13", "RD,  R13"]:
            return Standard.EN15804A1
        elif data == "D":
            return Standard.EN15804A2
        elif data == "D13":
            return Standard.EN15804A1
        elif data.strip() in ["Komb.", "Komb"]:
            return Standard.EN15804A2
        elif data == "Komb13":
            return Standard.EN15804A1
        elif data == "S":
            return Standard.UNKNOWN
        elif data == "E":
            return Standard.UNKNOWN
        elif data == "T":
            return Standard.UNKNOWN
        else:
            raise ValueError(f"Unknown standard: {data}")


class LCAxSubType:
    @classmethod
    def from_data_type(cls, data: str) -> SubType:
        if data is None:
            return SubType.GENERIC
        elif data == "R":
            return SubType.REPRESENTATIVE
        elif data == "R13":
            return SubType.REPRESENTATIVE
        elif data in ["R,R13", "R, R13", "RD,  R13"]:
            return SubType.REPRESENTATIVE
        elif data == "D":
            return SubType.GENERIC
        elif data == "D13":
            return SubType.GENERIC
        elif data.strip() in ["Komb.", "Komb"]:
            return SubType.GENERIC
        elif data == "Komb13":
            return SubType.GENERIC
        elif data == "S":
            return SubType.INDUSTRY
        elif data == "E":
            return SubType.INDUSTRY
        elif data == "T":
            return SubType.GENERIC
        else:
            raise ValueError(f"Unknown subtype: {data}")


class LCAxUnit:
    @classmethod
    def from_infralca(cls, unit: str) -> Unit:
        if unit == "t":
            return Unit.TONES
        elif unit == "kg":
            return Unit.KG
        elif unit == "m":
            return Unit.M
        elif unit == "m2":
            return Unit.M2
        elif unit == "m³":
            return Unit.M3
        elif unit in ["stk", "stk."]:
            return Unit.PCS
        elif unit == "kWh":
            return Unit.KWH
        elif unit == "l":
            return Unit.L
        elif unit == "tkm":
            return Unit.TONES_KM
        elif unit is None:
            return Unit.UNKNOWN
        else:
            raise ValueError(f"Unknown unit: {unit}")


def get_service_life(data: str | None) -> int | None:
    if data in ["-", "", " "] or data is None:
        return None
    else:
        return int(data)


def get_impact_data(data: tuple) -> dict:
    phases = [
        LifeCycleStage.A1A3,
        LifeCycleStage.C1,
        LifeCycleStage.C2,
        LifeCycleStage.C3,
        LifeCycleStage.C4,
        LifeCycleStage.D,
    ]
    categories = [
        ImpactCategoryKey.GWP,
        ImpactCategoryKey.GWP_FOS,
        ImpactCategoryKey.GWP_BIO,
        ImpactCategoryKey.GWP_LUL,
        ImpactCategoryKey.ODP,
        ImpactCategoryKey.AP,
        ImpactCategoryKey.EP_FW,
        ImpactCategoryKey.EP_MAR,
        ImpactCategoryKey.EP_TER,
        ImpactCategoryKey.POCP,
        ImpactCategoryKey.ADPE,
        ImpactCategoryKey.ADPF,
        ImpactCategoryKey.WDP,
    ]
    index = 0
    impacts = {}
    for phase in phases:
        impacts[phase.value] = {}
        for category in categories:
            impacts[phase.value][category.value] = data[index]
            index += 1

    return impacts


def get_epd_from_folder(name: str, path: Path) -> EPD:
    epd_file = path / "epds" / f"{str(uuid.uuid5(uuid.NAMESPACE_URL, name))}.json"
    if epd_file.exists():
        return EPD(**json.loads(epd_file.read_text()))
    else:
        raise FileNotFoundError(f"EPD file not found: {epd_file}")


def get_transport_epds(epds: list[list[str, float]], path: Path) -> list[EPD] | None:
    transports = None
    a4, a5 = epds[0], epds[1]
    if a4[0] is not None and a4[0] != '':
        epd = get_epd_from_folder(a4[0], path)
        transports = [
            Transport(
                distance=a4[1],
                distance_unit=Unit.KM,
                id=str(uuid.uuid4()),
                life_cycle_stages=[LifeCycleStage.A4],
                name=epd.name,
                impact_data=ImpactDataSource1(epd=epd)
            )
        ]
    if a5[0] is not None and a5[0] != '':
        epd = get_epd_from_folder(a5[0], path)
        transport = Transport(
                distance=a5[1],
                distance_unit=Unit.KM,
                id=str(uuid.uuid4()),
                life_cycle_stages=[LifeCycleStage.A5],
                name=epd.name,
                impact_data=ImpactDataSource1(epd=epd)
            )
        if transports is not None:
            transports.append(transport)
        else:
            transports = [transport]

    return transports


class LCAxEPD(EPD):
    @classmethod
    def from_row(cls, row: tuple, category: str, infralca_version: (str, date)) -> Self:
        return cls(
            comment=row[192],
            declared_unit=LCAxUnit.from_infralca(row[1]),
            format_version=importlib.metadata.version("lcax"),
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, row[0])),
            impacts=get_impact_data(row[3:87]),
            location=Country.DNK,
            meta_data={
                "category": category,
                "created": date.today().isoformat(),
                "origin": "https://github.com/ocni-dtu/infralca"
            },
            name=row[0],
            published_date=infralca_version[1],
            reference_service_life=get_service_life(row[305]),
            source=Source(name="InfraLCA"),
            standard=LCAxStandard.from_data_type(row[2]),
            subtype=LCAxSubType.from_data_type(row[2]),
            valid_until=infralca_version[1] + timedelta(days=365 * 5),
            version=infralca_version[0],
        )


class LCAxProduct(Product):
    @classmethod
    def from_row(cls, row: tuple, path: Path) -> Self:
        epd = get_epd_from_folder(row[0], path)
        return cls(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, row[0] + "_product")),
            impact_data=ImpactDataSource1(epd=epd),
            meta_data={
                "category": epd.meta_data.get("category"),
                "created": date.today().isoformat(),
                "origin": "https://github.com/ocni-dtu/infralca"
            },
            name=row[0],
            quantity=1,
            reference_service_life=epd.reference_service_life,
            results=None,
            transport=get_transport_epds([row[268:270], row[285:287]], path),
            unit=epd.declared_unit,
        )
