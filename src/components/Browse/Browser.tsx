import axios from 'axios';
import React, {useContext, useEffect, useState} from 'react';
import { AuthContext } from '../../Hooks/AuthProvider';

interface Record{
    id:string;
    diagnosis:string;
    treatment:string;
}
export const BrowseRecords:React.FC = () => {
    const [datalist,setDataList] = useState<Array<Record>>([]);
    const {port} = useContext(AuthContext);
    const renderdatalist = datalist.map(record => 
    <div id = {record.id}>
        <p>
            {record.id}
        </p>
        <p>
            {record.diagnosis}
        </p>
        <p>
            {record.treatment}
        </p>
    </div>
    )
    const url = `http://localhost:${port}/`;
    useEffect(()=>{
        try{
            axios.get(url).then((res)=>setDataList(res.data));
            console.log(datalist);
        }catch(e){
            console.log(e);
        }
    },[setDataList,url]);
    return (
        <>
            {renderdatalist}
        </>
    );
}
